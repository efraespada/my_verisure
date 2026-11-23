"""Connect pure notification consumers to entry-scoped read-only HA adapters.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from homeassistant.helpers import entity_registry as er

from .core.api.camera_client import CameraClient
from .core.api.device_manager import DeviceManager
from .core.api.notification_client import NotificationClient
from .core.api.provider_request_gate import get_provider_request_gate
from .core.application.alarm_state import AlarmState, analyze_alarm_state
from .core.application.notification_refresh import (
    BackgroundReadBudget,
    NotificationRefreshScheduler,
)
from .core.application.notification_verification import (
    NotificationReadDeferred,
    NotificationReadUnavailable,
    NotificationVerifier,
    VerifiedPhoto,
    has_smart_notifications,
)
from .core.application.notifications import NotificationHub, NotificationNotice
from .core.const import CONF_EXTERNAL_PHOTO_UPDATES, CONF_PUSH_STATE_REFRESH, DOMAIN

if TYPE_CHECKING:
    from .coordinator import MyVerisureDataUpdateCoordinator

_BUDGET_KEY = f"{DOMAIN}_notification_read_budget"


class NotificationRuntime:
    """Compose read ports lazily; constructors do not create tasks or sessions."""

    def __init__(
        self, coordinator: MyVerisureDataUpdateCoordinator, hub: NotificationHub
    ) -> None:
        self._coordinator, self._hub = coordinator, hub
        self._scheduler: NotificationRefreshScheduler | None = None
        self._closed = False
        self._seeded = False
        self.last_state_sync: float | None = None
        self._verifier = NotificationVerifier(
            hub,
            replay=hub,
            read_state=coordinator.async_refresh_current_alarm_state,
            read_incidents=self._read_incidents,
            read_photo=self._read_photo,
            incident_permission=lambda: has_smart_notifications(coordinator.data),
        )
        setter = getattr(
            coordinator.refresh_camera_images_use_case,
            "set_photo_committed_callback",
            None,
        )
        if callable(setter):
            setter(self._photo_committed)

    def activate(self) -> None:
        coordinator = self._coordinator
        if self._closed or self._scheduler is not None or not coordinator._push_enabled:
            return
        budget = coordinator.hass.data.setdefault(_BUDGET_KEY, BackgroundReadBudget())
        options = coordinator.config_entry.options
        self._scheduler = NotificationRefreshScheduler(
            self._verify,
            budget=budget,
            state_enabled=bool(options.get(CONF_PUSH_STATE_REFRESH, False)),
            external_photos=bool(options.get(CONF_EXTERNAL_PHOTO_UPDATES, False)),
            blocked_for=lambda: get_provider_request_gate().remaining_seconds,
        )
        self._hub.subscribe_hints(self._scheduler.submit)

    async def _verify(self, notice: NotificationNotice) -> bool:
        if notice.event.delivery == "reconciled":
            snapshot = await self._coordinator.async_refresh_current_alarm_state()
            if snapshot is None:
                return False
            self._verifier.seed_state(snapshot)
            self._seeded = True
            return True
        if not self._seeded:
            self._verifier.seed_state(self._coordinator.data)
            self._seeded = True
        return await self._verifier.verify(notice)

    async def _read_incidents(
        self, notice: NotificationNotice
    ) -> tuple[str, ...] | None:
        coordinator = self._coordinator
        state = coordinator._get_operation_state()
        if state.lock.locked():
            raise NotificationReadDeferred
        generation = state.generation
        if not await coordinator.async_login():
            return None
        panel, caps = await coordinator._async_ensure_installation_context()
        if not has_smart_notifications(coordinator.data):
            raise NotificationReadUnavailable
        if generation != state.generation or state.lock.locked():
            raise NotificationReadDeferred
        auth_hash = getattr(coordinator.session_manager, "hash_token", None)
        root = coordinator.composition_root
        result = await NotificationClient(
            coordinator.session_manager, root.get(DeviceManager).profile_context
        ).get_open_incidents(coordinator.installation_id, panel, caps)
        if (
            generation != state.generation
            or state.lock.locked()
            or auth_hash != getattr(coordinator.session_manager, "hash_token", None)
        ):
            return None
        return result

    def _camera_entity(self, identifier: str) -> str | None:
        coordinator = self._coordinator
        from .camera import camera_unique_id

        devices = (
            (coordinator.data or {})
            .get("detailed_installation", {})
            .get("installation", {})
            .get("devices", [])
        )
        for device in devices:
            try:
                candidate = f"{device['type']}{int(device['code']):02d}"
                if candidate == identifier and device.get("is_active") is not False:
                    return er.async_get(coordinator.hass).async_get_entity_id(
                        "camera",
                        DOMAIN,
                        camera_unique_id(coordinator.config_entry.entry_id, device),
                    )
            except (KeyError, TypeError, ValueError):
                continue
        return None

    async def _read_photo(self, notice: NotificationNotice) -> VerifiedPhoto | None:
        coordinator = self._coordinator
        assert notice.signal_id and notice.event.occurred_at is not None
        state = coordinator._get_operation_state()
        if coordinator._camera_refresh_lock.locked() or state.lock.locked():
            raise NotificationReadDeferred
        async with coordinator._camera_refresh_lock:
            if not await coordinator.async_login():
                raise NotificationReadDeferred
            panel, caps = await coordinator._async_ensure_installation_context()
            generation = state.generation
            if state.lock.locked():
                raise NotificationReadDeferred
            devices = (
                (coordinator.data or {})
                .get("detailed_installation", {})
                .get("installation", {})
                .get("devices", [])
            )
            codes = []
            for device in devices:
                try:
                    if (
                        device.get("type") in {"YR", "YP"}
                        and device.get("is_active") is not False
                    ):
                        codes.append(f"{device['type']}{int(device['code']):02d}")
                except (KeyError, TypeError, ValueError):
                    continue
            result = await coordinator.composition_root.get(
                CameraClient
            ).get_existing_photo(
                coordinator.installation_id,
                panel,
                caps,
                signal_id=notice.signal_id,
                expected_camera_codes=codes,
                event_timestamp=notice.event.occurred_at,
            )
            if generation != state.generation or state.lock.locked():
                raise NotificationReadDeferred
            if not result or result.get("success") is not True:
                return None
            subject = self._camera_entity(result["camera_identifier"])
            if not subject:
                return None
            coordinator.async_update_listeners()
            return VerifiedPhoto(subject, result["images_saved"])

    def _photo_committed(self, camera: str, count: int, signal: str | None) -> None:
        if self._closed:
            return
        subject = self._camera_entity(camera)
        if subject:
            self._verifier.publish_photo(
                VerifiedPhoto(subject, count),
                signal_id=signal,
                correlation_id=self._hub.correlation_for_signal(signal),
                origin="local_request",
            )

    def diagnostics(self) -> dict[str, int]:
        return self._scheduler.diagnostics() if self._scheduler else {}

    def state_synchronized(self, snapshot: dict) -> None:
        """Track only a freshly committed authoritative state, never a cache load."""
        if (
            analyze_alarm_state(snapshot.get("alarm_status", {})).state
            != AlarmState.UNKNOWN
        ):
            self.last_state_sync = time.time()

    def command_completed(self, snapshot: dict, reference: str | None) -> None:
        if not self._closed:
            self._verifier.confirm_local_state(snapshot, correlation_id=reference)
            self._seeded = True

    async def async_close(self) -> None:
        self._closed = True
        setter = getattr(
            self._coordinator.refresh_camera_images_use_case,
            "set_photo_committed_callback",
            None,
        )
        if callable(setter):
            setter(None)
        if self._scheduler is not None:
            await self._scheduler.async_close()

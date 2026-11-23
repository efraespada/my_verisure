"""Entry-scoped push activation and native profile reconciliation.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .core.api.device_manager import DeviceManager, PushTokenStage
from .core.api.notification_mapper import NotificationMapper
from .core.api.provider_request_gate import get_provider_request_gate
from .core.api.push_receiver import PushReceiver
from .core.application.notifications import NotificationHub
from .core.application.photo_notifications import PhotoNotifications
from .core.const import CONF_NOTIFICATION_OBSERVATION
from .core.dependency_injection.composition_root import CompositionRoot
from .core.file_manager import FileManager
from .core.session_manager import SessionManager
from .core.utils.jwt_utils import get_jwt_payload
from .notification_context import NOTIFICATION_CONTEXT

_LOGGER = logging.getLogger(__name__)


async def async_reconcile_profile(
    device: DeviceManager,
    session: SessionManager,
) -> None:
    """Load the persisted profile before considering a cached access session."""
    await device.async_ensure_device_identifiers()
    payload = get_jwt_payload(session.hash_token or "") or {}
    callby = payload.get("callBy", payload.get("callby"))
    if callby and callby != device.profile_context.current.callby:
        session.hash_token = None
        session.refresh_token = None


class HomeAssistantPush:
    """Prepare once, retain the token and stop all tasks on entry unload."""

    def __init__(
        self,
        hass: HomeAssistant,
        root: CompositionRoot,
        *,
        enabled: bool = True,
        installation_id: str = "",
        entry_id: str = "",
        options: dict | None = None,
    ) -> None:
        self._hass = hass
        self._root = root
        self._lock = asyncio.Lock()
        self._finish_lock = asyncio.Lock()
        self._retry_at = 0.0
        self._enabled = enabled
        self._closed = False
        self._latest_token: str | None = None
        self._stage: PushTokenStage | None = None
        self._session_before: tuple[dict[str, object], bytes | None] | None = None
        self.receiver: PushReceiver | None = None
        self.hub = NotificationHub(
            entry_id,
            NotificationMapper(installation_id, entry_id),
            root.get(PhotoNotifications) if enabled else None,
            observation_enabled=(options or {}).get(
                CONF_NOTIFICATION_OBSERVATION, True
            ),
        )
        self.hub.set_binding_state("pending" if enabled else "disabled")

    def _token_changed(self, token: str) -> None:
        if not self._closed:
            self._latest_token = token
            self.hub.set_binding_state("pending")

    async def async_prepare(self) -> None:
        """Register before login; a failed receiver leaves polling available."""
        if not self._enabled or self._closed:
            return
        async with self._lock:
            if self._closed or time.monotonic() < self._retry_at:
                return
            if self.receiver is None:
                self.receiver = PushReceiver(
                    self._root.get(FileManager),
                    self.hub,
                    http_session=async_get_clientsession(self._hass),
                    on_token_changed=self._token_changed,
                )
                self.hub.subscribe_diagnostics(self.receiver.request_state_save)
            try:
                token = await self.receiver.async_prepare()
                self._latest_token = token
                if self._closed:
                    return
                device = self._root.get(DeviceManager)
                if self._stage is None:
                    session = self._root.get(SessionManager)
                    previous = device.profile_context.current.callby
                    self._session_before = (
                        await session.async_capture_transaction_state()
                    )
                    self._stage, changed = await device.async_stage_push_token(token)
                    if changed:
                        session.hash_token = None
                        if previous != "OWA_10":
                            session.refresh_token = None
                        self.hub.set_binding_state("pending")
                context_token = NOTIFICATION_CONTEXT.set(None)
                try:
                    await self.receiver.async_start()
                finally:
                    NOTIFICATION_CONTEXT.reset(context_token)
            except asyncio.CancelledError:
                await self.async_finish_auth(False)
                raise
            except Exception:
                await self.async_finish_auth(False)
                self._retry_at = time.monotonic() + 900
                self.hub.set_binding_state("degraded")
                _LOGGER.warning("Push setup unavailable; polling remains enabled")

    async def async_finish_auth(self, accepted: bool) -> None:
        """Keep durable device and session changes within one owned transaction."""

        async def finish() -> None:
            async with self._finish_lock:
                await self._finish_auth_locked(accepted and not self._closed)

        await self._drain_owned(finish(), "my_verisure_push_binding")

    async def _finish_auth_locked(self, accepted: bool) -> None:
        stage, before = self._stage, self._session_before
        if stage is None:
            return
        assert before is not None
        device = self._root.get(DeviceManager)
        session = self._root.get(SessionManager)
        try:
            if accepted:
                await device.async_commit_staged_push_token(stage)
                self.hub.set_binding_state(
                    "bound"
                    if stage.candidate_token == self._latest_token
                    else "pending"
                )
            else:
                await device.async_rollback_staged_push_token(stage)
                await session.async_restore_transaction_state(*before)
                self._retry_at = time.monotonic() + 900
                self.hub.set_binding_state("reauth_required")
        except BaseException:
            await device.async_rollback_staged_push_token(stage)
            await session.async_restore_transaction_state(*before)
            self.hub.set_binding_state("degraded")
            raise
        finally:
            self._stage = None
            self._session_before = None

    @staticmethod
    async def _drain_owned(coroutine: Any, name: str) -> None:
        owner = asyncio.create_task(coroutine, name=name)
        cancelled = False
        while not owner.done():
            try:
                await asyncio.shield(owner)
            except asyncio.CancelledError:
                cancelled = True
        owner.result()
        if cancelled:
            raise asyncio.CancelledError

    async def async_stop(self) -> None:
        """Cancel listener and pending push waits before unloading the entry."""
        self._closed = True

        async def stop() -> None:
            async with self._lock:
                await self.async_finish_auth(False)
                try:
                    if self.receiver is not None:
                        await self.receiver.async_stop()
                finally:
                    self.hub.close()

        await self._drain_owned(stop(), "my_verisure_push_stop")

    def diagnostics(self) -> dict[str, Any]:
        """Return counters and connection state, never credentials or tokens."""
        return {
            **self.hub.diagnostics(),
            "enabled": self._enabled,
            "transport": self.receiver.diagnostics() if self.receiver else {},
            "cooldown_remaining": get_provider_request_gate().remaining_seconds,
        }

"""Confirm reported notifications through explicit read-only application ports.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
import re
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .notifications import NotificationNotice


def has_smart_notifications(snapshot: object) -> bool:
    """Mirror the native service-520 active/visible permission without role guesses."""
    detailed = (
        snapshot.get("detailed_installation") if isinstance(snapshot, Mapping) else None
    )
    installation = (
        detailed.get("installation") if isinstance(detailed, Mapping) else None
    )
    services = (
        installation.get("services") if isinstance(installation, Mapping) else None
    )
    return isinstance(services, list) and any(
        isinstance(service, Mapping)
        and service.get("id_service") == "520"
        and service.get("active") is True
        and service.get("visible") is True
        for service in services
    )


class VerificationPublisher(Protocol):
    """Small publication seam; the hub owns correlation, public IDs and timestamps."""

    def publish_verified(
        self,
        kind: str,
        *,
        correlation_id: str | None = None,
        facts: dict[str, Any] | None = None,
        subject_entity_id: str | None = None,
        verification: str = "authoritative_read",
        deduplication_key: str | None = None,
    ) -> object: ...


class VerificationReplay(Protocol):
    """Keep bounded resource state without projecting provider identifiers publicly."""

    def get_resource_state(self, key: str) -> str | None: ...

    def set_resource_state(self, key: str, state: str) -> None: ...


class NotificationReadDeferred(Exception):
    """A transient operation/epoch conflict requires one coalesced later read."""


class NotificationReadUnavailable(Exception):
    """A definitive context/permission rejection consumes a hint without facts."""


@dataclass(frozen=True)
class VerifiedPhoto:
    """A camera-adapter result emitted only after every expected image was saved."""

    subject_entity_id: str
    image_count: int


StateReader = Callable[[], Awaitable[dict[str, Any] | None]]
IncidentReader = Callable[["NotificationNotice"], Awaitable[tuple[str, ...] | None]]
PhotoReader = Callable[["NotificationNotice"], Awaitable[VerifiedPhoto | None]]


class NotificationVerifier:
    """Turn explicitly scoped live hints into confirmed facts, never commands."""

    def __init__(
        self,
        hub: VerificationPublisher,
        *,
        read_state: StateReader | None = None,
        read_incidents: IncidentReader | None = None,
        read_photo: PhotoReader | None = None,
        incident_permission: Callable[[], bool] | None = None,
        is_local_operation: Callable[[NotificationNotice], bool] | None = None,
        replay: VerificationReplay | None = None,
    ) -> None:
        self._hub = hub
        self._read_state = read_state
        self._read_incidents = read_incidents
        self._read_photo = read_photo
        self._incident_permission = incident_permission or (lambda: False)
        self._is_local_operation = is_local_operation or (lambda notice: False)
        self._replay = replay
        self._state: tuple[bool, bool, bool, bool] | None = None
        self._incidents: OrderedDict[str, str] = OrderedDict()
        self._photos: OrderedDict[tuple[str, str], None] = OrderedDict()

    def seed_state(self, snapshot: object) -> bool:
        """Initialize display baseline from a known snapshot without firing an event."""
        self._state = self._state_signature(snapshot)
        return self._state is not None

    def confirm_local_state(
        self, snapshot: object, *, correlation_id: str | None = None
    ) -> bool:
        """Publish a known command result without performing another provider read."""
        alarm = snapshot.get("alarm_status") if isinstance(snapshot, Mapping) else None
        state = self._state_signature(snapshot)
        code = (
            {
                (False, False, False, False): "D",
                (False, False, False, True): "E",
                (False, True, False, False): "Q",
                (False, True, False, True): "C",
            }.get(state)
            if state is not None
            else None
        )
        if (
            not isinstance(alarm, Mapping)
            or alarm.get("success") is not True
            or state is None
            or code is None
        ):
            return False
        facts = dict(
            zip(("internal_day", "internal_night", "internal_total", "external"), state)
        )
        self._hub.publish_verified(
            "alarm_state_confirmed",
            correlation_id=correlation_id,
            facts={**facts, "alarm_state": code, "origin": "local_request"},
            verification="command_result",
        )
        self._state = state
        return True

    @staticmethod
    def _state_signature(snapshot: object) -> tuple[bool, bool, bool, bool] | None:
        alarm = snapshot.get("alarm_status") if isinstance(snapshot, Mapping) else None
        data = alarm.get("data") if isinstance(alarm, Mapping) else None
        internal = data.get("internal") if isinstance(data, Mapping) else None
        external = data.get("external") if isinstance(data, Mapping) else None
        if not isinstance(internal, Mapping) or not isinstance(external, Mapping):
            return None
        values = []
        for mode in ("day", "night", "total"):
            section = internal.get(mode)
            values.append(
                section.get("status") if isinstance(section, Mapping) else None
            )
        values.append(external.get("status"))
        day, night, total, external_status = values
        if (
            not isinstance(day, bool)
            or not isinstance(night, bool)
            or not isinstance(total, bool)
            or not isinstance(external_status, bool)
        ):
            return None
        return day, night, total, external_status

    async def verify(self, notice: NotificationNotice) -> bool:
        """Return False only when a read was superseded and should stay pending."""
        event = notice.event
        if (
            event.scope != "installation"
            or event.delivery != "live"
            or event.freshness == "stale"
        ):
            return True
        try:
            if event.kind in {
                "alarm_operation_reported",
                "arm_reminder",
                "unprotected_home",
                "smart_disarm_notice",
            }:
                return await self._verify_state(notice)
            if event.kind == "security_incident_reported":
                return await self._verify_incident(notice)
            if event.kind == "photo_reported":
                return await self._verify_photo(notice)
        except NotificationReadDeferred:
            return False
        except NotificationReadUnavailable:
            return True
        return True

    async def _verify_state(self, notice: NotificationNotice) -> bool:
        if self._read_state is None:
            return True
        snapshot = await self._read_state()
        if snapshot is None:
            return False
        state = self._state_signature(snapshot)
        previous = self._state
        local_operation = bool(notice.operation_id) and self._is_local_operation(notice)
        if (
            state is None
            or state == previous
            or previous is None
            and not local_operation
        ):
            self._state = state
            return True
        facts: dict[str, Any] = dict(
            zip(("internal_day", "internal_night", "internal_total", "external"), state)
        )
        code = {
            (False, False, False, False): "D",
            (False, False, False, True): "E",
            (False, True, False, False): "Q",
            (False, True, False, True): "C",
        }.get(state)
        if code is not None:
            facts["alarm_state"] = code
        self._hub.publish_verified(
            "alarm_state_confirmed",
            correlation_id=notice.event.correlation_id,
            facts=facts,
        )
        self._state = state
        return True

    async def _verify_incident(self, notice: NotificationNotice) -> bool:
        signal = notice.signal_id
        if (
            self._read_incidents is None
            or not self._incident_permission()
            or not signal
        ):
            return True
        incidents = await self._read_incidents(notice)
        if incidents is None:
            return False
        state = "open" if signal in incidents else "not_listed"
        key = "incident:" + signal
        previous = self._incidents.get(signal)
        if previous is None and self._replay is not None:
            previous = self._replay.get_resource_state(key)
        if previous != state:
            self._hub.publish_verified(
                "incident_status_confirmed",
                correlation_id=notice.event.correlation_id,
                facts={"incident_state": state},
            )
        self._incidents[signal] = state
        self._incidents.move_to_end(signal)
        if len(self._incidents) > 128:
            self._incidents.popitem(last=False)
        if self._replay is not None:
            self._replay.set_resource_state(key, state)
        return True

    async def _verify_photo(self, notice: NotificationNotice) -> bool:
        if (
            self._read_photo is None
            or not notice.signal_id
            or notice.photo_type != 0
            or notice.event.freshness != "fresh"
            or notice.event.occurred_at is None
        ):
            return True
        if any(signal == notice.signal_id for subject, signal in self._photos):
            return True
        photo = await self._read_photo(notice)
        if photo is None:
            return True
        self.publish_photo(
            photo,
            signal_id=notice.signal_id,
            correlation_id=notice.event.correlation_id,
            origin="provider_notice",
        )
        return True

    def publish_photo(
        self,
        photo: VerifiedPhoto,
        *,
        signal_id: str | None = None,
        correlation_id: str | None = None,
        origin: str = "unknown",
    ) -> bool:
        """Publish a saved photo through one bounded deduplication seam."""
        if (
            not re.fullmatch(r"camera\.[a-z0-9_]{1,200}", photo.subject_entity_id)
            or type(photo.image_count) is not int
            or not 1 <= photo.image_count <= 8
        ):
            return False
        key = (photo.subject_entity_id, signal_id) if signal_id else None
        if key is not None and key in self._photos:
            return False
        if origin not in {
            "unknown",
            "local_request",
            "provider_notice",
            "reconciliation",
        }:
            origin = "unknown"
        published = self._hub.publish_verified(
            "photo_ready",
            correlation_id=correlation_id,
            subject_entity_id=photo.subject_entity_id,
            facts={"image_count": photo.image_count, "origin": origin},
            verification="image_commit",
            deduplication_key=f"photo:{photo.subject_entity_id}:{signal_id}"
            if signal_id
            else None,
        )
        if key is not None:
            self._photos[key] = None
            if len(self._photos) > 128:
                self._photos.popitem(last=False)
        return published is not None

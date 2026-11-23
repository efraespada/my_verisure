"""Entry-owned notification admission, safe records and independent consumers.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from collections import Counter, OrderedDict, deque
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Protocol

from .alarm_status_service import KNOWN_PANEL_CODES
from .photo_notifications import PhotoNotifications

REPORTED_KINDS = (
    "photo_reported",
    "alarm_operation_reported",
    "security_incident_reported",
    "arm_reminder",
    "unprotected_home",
    "smart_disarm_notice",
    "device_maintenance_notice",
    "device_tamper_reported",
    "maintenance_appointment",
    "support_reply",
    "account_notice",
    "generic_notice",
    "unclassified_notice",
)
CONFIRMED_KINDS = ("photo_ready", "alarm_state_confirmed", "incident_status_confirmed")
BINDING_STATES = ("disabled", "pending", "bound", "reauth_required", "degraded")
_REPLAY_LIMIT = 512
_REPLAY_TTL = 86400


def _iso(value: float | None) -> str | None:
    return (
        datetime.fromtimestamp(value, timezone.utc).isoformat()
        if value is not None
        else None
    )


def opaque_id(namespace: str, value: str) -> str:
    """Create a local identifier without exposing provider delivery/correlation IDs."""
    return hashlib.sha256(f"{namespace}\0{value}".encode()).hexdigest()


def _safe_facts(facts: dict[str, Any] | None) -> tuple[tuple[str, Any], ...]:
    result: dict[str, Any] = {}
    for key, value in (facts or {}).items():
        if key in {"internal_day", "internal_night", "internal_total", "external"}:
            if value is None or isinstance(value, bool):
                result[key] = value
        elif key == "image_count" and type(value) is int and 0 <= value <= 8:
            result[key] = value
        elif key == "incident_state" and value in ("open", "not_listed"):
            result[key] = value
        elif (
            key == "alarm_state"
            and isinstance(value, str)
            and value in KNOWN_PANEL_CODES
        ):
            result[key] = value
        elif (
            key == "origin"
            and isinstance(value, str)
            and value
            in {
                "local_request",
                "provider_notice",
                "reconciliation",
                "unknown",
            }
        ):
            result[key] = value
    return tuple(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class NotificationEvent:
    kind: str
    stage: str
    event_id: str
    correlation_id: str
    category: str
    scope: str
    received_at: float
    provider_request: str | None = None
    occurred_at: float | None = None
    verified_at: float | None = None
    freshness: str = "unknown"
    delivery: str = "live"
    verification: str = "notification_only"
    subject_entity_id: str | None = None
    facts: tuple[tuple[str, Any], ...] = ()

    def public_data(self) -> dict[str, Any]:
        """Project only the explicitly safe, versioned HA event contract."""
        return {
            "schema_version": 1,
            "event_id": self.event_id,
            "correlation_id": self.correlation_id,
            "kind": self.kind,
            "stage": self.stage,
            "category": self.category,
            "scope": self.scope,
            "provider_request": self.provider_request,
            "received_at": _iso(self.received_at),
            "occurred_at": _iso(self.occurred_at),
            "verified_at": _iso(self.verified_at),
            "freshness": self.freshness,
            "delivery": self.delivery,
            "verification": self.verification,
            "subject_entity_id": self.subject_entity_id,
            **dict(self.facts),
        }


@dataclass(frozen=True, slots=True)
class NotificationNotice:
    """Private correlation fields stay outside the public event projection."""

    event: NotificationEvent
    signal_id: str | None = None
    operation_id: str | None = None
    photo_type: int | None = None


@dataclass(frozen=True, slots=True)
class NotificationMapping:
    notice: NotificationNotice | None
    reason: str


class NotificationMapperPort(Protocol):
    def __call__(
        self, payload: dict[str, Any], persistent_id: str, now: float
    ) -> NotificationMapping: ...


class NotificationHub:
    """Own bounded replay, readiness and safe fan-out for a single config entry."""

    def __init__(
        self,
        namespace: str,
        mapper: NotificationMapperPort,
        photos: PhotoNotifications | None = None,
        *,
        clock: Callable[[], float] = time.time,
        observation_enabled: bool = True,
    ) -> None:
        self._namespace, self._mapper, self._photos, self._clock = (
            namespace,
            mapper,
            photos,
            clock,
        )
        self._observation_enabled = observation_enabled
        self._ready = self._closed = self._connected = False
        self._ever_connected = False
        self._recovery_cutoff: float | None = None
        self._binding_state = "pending"
        self._seen: OrderedDict[str, float] = OrderedDict()
        self._resources: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._raw_ids: deque[str] = deque(maxlen=128)
        self._photo_correlations: OrderedDict[str, str] = OrderedDict()
        self._recent: deque[dict[str, Any]] = deque(maxlen=100)
        self._buffer: deque[NotificationEvent] = deque()
        self._buffer_bytes = 0
        self._listeners: list[Callable[[NotificationEvent], None]] = []
        self._hints: list[Callable[[NotificationNotice], None]] = []
        self._health: list[Callable[[], None]] = []
        self._counts: Counter[str] = Counter()
        self._coverage: Counter[str] = Counter()
        self._last_received: float | None = None
        self._last_accepted: float | None = None
        self._last_verified: float | None = None

    @property
    def connected(self) -> bool:
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        recovered = bool(value) and not self._connected and self._ever_connected
        self._connected = bool(value)
        self._ever_connected = self._ever_connected or self._connected
        if self._connected and (recovered or self._recovery_cutoff is None):
            self._recovery_cutoff = self._clock()
        if self._photos is not None:
            self._photos.connected = self._connected
        self._notify_health()
        if recovered and self._ready:
            # This internal read hint is never a provider notice or public event.
            identity = opaque_id(self._namespace, "reconcile:" + uuid.uuid4().hex)
            notice = NotificationNotice(
                NotificationEvent(
                    "alarm_operation_reported",
                    "reported",
                    identity,
                    identity,
                    "alarm",
                    "installation",
                    self._clock(),
                    delivery="reconciled",
                )
            )
            self._deliver_hint(notice)

    @property
    def recent_ids(self) -> list[str]:
        return list(self._raw_ids)

    def restore_ids(self, values: list[str]) -> None:
        self._raw_ids.extend(
            v for v in values[-128:] if isinstance(v, str) and 0 < len(v) <= 512
        )
        if self._photos is not None:
            self._photos.restore_ids(list(self._raw_ids))
        for value in self._raw_ids:
            self._remember(
                opaque_id(self._namespace, "delivery:" + value), self._clock()
            )

    def export_replay(self) -> dict[str, Any]:
        self._expire()
        return {
            "version": 1,
            "seen": [[key, stamp] for key, stamp in self._seen.items()],
            "resources": [
                [key, state, stamp] for key, (state, stamp) in self._resources.items()
            ],
        }

    def restore_replay(self, value: dict[str, Any]) -> None:
        if (
            type(value.get("version")) is not int
            or value["version"] != 1
            or not isinstance(value.get("seen"), list)
        ):
            return
        now = self._clock()
        for item in value["seen"][-_REPLAY_LIMIT:]:
            if not isinstance(item, list) or len(item) != 2:
                continue
            key, stamp = item
            if (
                isinstance(key, str)
                and re.fullmatch(r"[a-f0-9]{64}", key)
                and type(stamp) in (int, float)
                and math.isfinite(stamp)
                and now - _REPLAY_TTL <= stamp <= now + 60
            ):
                self._remember(key, float(stamp))
        resources = value.get("resources", [])
        if not isinstance(resources, list):
            return
        for item in resources[-128:]:
            if not isinstance(item, list) or len(item) != 3:
                continue
            key, state, stamp = item
            if (
                isinstance(key, str)
                and re.fullmatch(r"[a-f0-9]{64}", key)
                and state in ("open", "not_listed")
                and type(stamp) in (int, float)
                and math.isfinite(stamp)
                and now - _REPLAY_TTL <= stamp <= now + 60
            ):
                self._resources[key] = state, float(stamp)
        while len(self._resources) > 128:
            self._resources.popitem(last=False)

    def get_resource_state(self, key: str) -> str | None:
        self._expire()
        value = self._resources.get(opaque_id(self._namespace, "resource:" + key))
        return value[0] if value is not None else None

    def set_resource_state(self, key: str, state: str) -> None:
        if self._closed:
            return
        if (
            not isinstance(key, str)
            or not 0 < len(key) <= 256
            or state not in ("open", "not_listed")
        ):
            raise ValueError("Invalid private resource state")
        identity = opaque_id(self._namespace, "resource:" + key)
        self._resources[identity] = state, self._clock()
        self._resources.move_to_end(identity)
        if len(self._resources) > 128:
            self._resources.popitem(last=False)
        self._notify_health()

    def _expire(self) -> None:
        cutoff = self._clock() - _REPLAY_TTL
        for key, stamp in list(self._seen.items()):
            if stamp < cutoff:
                self._seen.pop(key, None)
        for key, (_, stamp) in list(self._resources.items()):
            if stamp < cutoff:
                self._resources.pop(key, None)

    def _remember(self, key: str, stamp: float) -> None:
        self._seen[key] = stamp
        self._seen.move_to_end(key)
        while len(self._seen) > _REPLAY_LIMIT:
            self._seen.popitem(last=False)

    def _subscribe(self, collection: list, callback: Callable) -> Callable[[], None]:
        if not self._closed:
            collection.append(callback)

        def remove() -> None:
            if callback in collection:
                collection.remove(callback)

        return remove

    def subscribe(
        self, callback: Callable[[NotificationEvent], None]
    ) -> Callable[[], None]:
        return self._subscribe(self._listeners, callback)

    def subscribe_hints(
        self, callback: Callable[[NotificationNotice], None]
    ) -> Callable[[], None]:
        return self._subscribe(self._hints, callback)

    def subscribe_diagnostics(self, callback: Callable[[], None]) -> Callable[[], None]:
        return self._subscribe(self._health, callback)

    def _notify_health(self) -> None:
        for callback in tuple(self._health):
            try:
                callback()
            except Exception:
                self._counts["consumer_failed"] += 1

    def _deliver(self, event: NotificationEvent) -> None:
        if self._observation_enabled:
            for callback in tuple(self._listeners):
                try:
                    callback(event)
                except Exception:
                    self._counts["consumer_failed"] += 1

    def _deliver_hint(self, notice: NotificationNotice) -> None:
        for callback in tuple(self._hints):
            try:
                callback(notice)
            except Exception:
                self._counts["consumer_failed"] += 1

    def activate(self) -> None:
        """Finish startup without turning buffered display into new automation."""
        self._buffer.clear()
        self._buffer_bytes = 0
        self._ready = not self._closed
        self._notify_health()

    def set_binding_state(self, value: str) -> None:
        if value not in BINDING_STATES:
            raise ValueError("Invalid notification binding state")
        self._binding_state = value
        self._notify_health()

    def receive(self, payload: dict[str, Any], persistent_id: str) -> None:
        if self._closed:
            return
        now = self._clock()
        self._last_received = now
        self._counts["received"] += 1
        if not isinstance(persistent_id, str) or not 0 < len(persistent_id) <= 512:
            self._counts["malformed"] += 1
            self._notify_health()
            return
        self._expire()
        identity = opaque_id(self._namespace, "delivery:" + persistent_id)
        if identity in self._seen:
            self._counts["duplicate"] += 1
            self._notify_health()
            return
        self._raw_ids.append(persistent_id)
        self._remember(identity, now)
        mapped = self._mapper(payload, persistent_id, now)
        if mapped.notice is None:
            self._counts[mapped.reason] += 1
            self._notify_health()
            return
        notice, event = mapped.notice, mapped.notice.event
        if (
            notice.signal_id
            and event.provider_request == "INF"
            and event.scope == "installation"
        ):
            self._photo_correlations[notice.signal_id] = event.correlation_id
            self._photo_correlations.move_to_end(notice.signal_id)
            if len(self._photo_correlations) > 128:
                self._photo_correlations.popitem(last=False)
        if (
            self._recovery_cutoff is not None
            and event.occurred_at is not None
            and event.occurred_at <= self._recovery_cutoff
        ):
            event = replace(event, delivery="reconciled")
            notice = replace(notice, event=event)
            self._counts["reconciled"] += 1
        self._counts["accepted"] += 1
        self._last_accepted = now
        self._coverage[event.provider_request or "unclassified"] += 1
        if event.kind == "unclassified_notice":
            self._counts["unclassified"] += 1
        if event.scope != "installation":
            self._counts["unassigned"] += 1
        if event.freshness == "stale":
            self._counts["stale"] += 1
        if not self._ready:
            event = replace(event, delivery="buffered")
            size = len(json.dumps(event.public_data()).encode())
            while self._buffer and (
                len(self._buffer) >= 64 or self._buffer_bytes + size > 131072
            ):
                removed = self._buffer.popleft()
                self._buffer_bytes -= len(json.dumps(removed.public_data()).encode())
                self._counts["buffer_dropped"] += 1
            self._buffer.append(event)
            self._buffer_bytes += size
        self._recent.append(event.public_data())
        # The pending photo uses its own exact camera/time verification. Do not
        # delay it behind UI startup or slow provider reconciliation.
        pending_photo = self._photos is not None and self._photos.pending
        if (
            self._photos is not None
            and notice.event.provider_request == "INF"
            and event.scope == "installation"
        ):
            self._photos.receive(payload, persistent_id)
        eligible = (
            self._ready
            and event.scope == "installation"
            and event.freshness != "stale"
            and event.delivery == "live"
        )
        if eligible:
            self._deliver(event)
            if event.kind != "unclassified_notice" and not (
                pending_photo and event.kind == "photo_reported"
            ):
                self._deliver_hint(notice)
        self._notify_health()

    def publish_verified(
        self,
        kind: str,
        *,
        correlation_id: str | None = None,
        facts: dict[str, Any] | None = None,
        subject_entity_id: str | None = None,
        delivery: str = "live",
        verification: str = "authoritative_read",
        timestamp: float | None = None,
        deduplication_key: str | None = None,
    ) -> NotificationEvent | None:
        if self._closed:
            return None
        if kind not in CONFIRMED_KINDS:
            raise ValueError("Unsupported confirmed notification kind")
        if delivery not in {"live", "buffered", "restored", "reconciled"}:
            raise ValueError("Invalid notification delivery state")
        if verification not in {"authoritative_read", "image_commit", "command_result"}:
            raise ValueError("Unsupported notification verification method")
        now = self._clock() if timestamp is None else timestamp
        if (
            type(now) not in (float, int)
            or not math.isfinite(now)
            or not 0 <= now <= 253402300799
        ):
            raise ValueError("Invalid notification verification time")
        correlation = correlation_id or uuid.uuid4().hex
        if not re.fullmatch(r"[a-f0-9]{64}", correlation):
            correlation = opaque_id(self._namespace, correlation)
        safe = _safe_facts(facts)
        if deduplication_key is not None and (
            not isinstance(deduplication_key, str)
            or not 0 < len(deduplication_key) <= 1024
        ):
            raise ValueError("Invalid private notification deduplication key")
        identity = opaque_id(
            self._namespace,
            f"{kind}:key:{deduplication_key}"
            if deduplication_key is not None
            else f"{kind}:{correlation}:{safe!r}",
        )
        self._expire()
        if identity in self._seen:
            self._counts["duplicate"] += 1
            return None
        self._remember(identity, float(now))
        subject = (
            subject_entity_id
            if isinstance(subject_entity_id, str)
            and re.fullmatch(r"[a-z_]+\.[a-z0-9_]{1,128}", subject_entity_id)
            else None
        )
        event = NotificationEvent(
            kind,
            "confirmed",
            identity,
            correlation,
            {
                "photo_ready": "photo",
                "alarm_state_confirmed": "alarm",
                "incident_status_confirmed": "incident",
            }[kind],
            "installation",
            float(now),
            verified_at=float(now),
            freshness="fresh",
            delivery=delivery,
            verification=verification,
            subject_entity_id=subject,
            facts=safe,
        )
        self._last_verified = float(now)
        self._recent.append(event.public_data())
        if self._ready and delivery == "live":
            self._deliver(event)
        self._notify_health()
        return event

    def correlation_for_signal(self, signal_id: str | None) -> str | None:
        """Retain only bounded private photo correlation, without guessing actors."""
        return self._photo_correlations.get(signal_id) if signal_id else None

    def diagnostics(self) -> dict[str, Any]:
        return {
            "connected": self._connected,
            "binding_state": self._binding_state,
            "last_received": self._last_received,
            "last_accepted": self._last_accepted,
            "last_verified": self._last_verified,
            "counters": dict(self._counts),
            "coverage": dict(self._coverage),
            "recent": list(self._recent),
        }

    def close(self) -> None:
        self._closed = True
        self.connected = False
        if self._photos is not None:
            self._photos.close()
        self._listeners.clear()
        self._hints.clear()
        self._health.clear()
        self._buffer.clear()
        self._buffer_bytes = 0

"""Loop-owned provider admission, shared cooldown and installation operations.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import asyncio
import hashlib
import math
import time
import weakref
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime

from ..application.exceptions import MyVerisureServiceBlockedError

DEFAULT_BLOCKED_COOLDOWN_SECONDS = 600.0
_LOOP_GATE_ATTRIBUTE = "_my_verisure_provider_request_gate"


def retry_after_seconds(value: object, now: float) -> float:
    """Read RFC delta-seconds or an aware HTTP date without retaining the header."""
    if not isinstance(value, str) or not 0 < len(value) <= 128:
        return DEFAULT_BLOCKED_COOLDOWN_SECONDS
    value = value.strip()
    if value.isascii() and value.isdigit():
        seconds = float(value)
        return seconds if math.isfinite(seconds) else DEFAULT_BLOCKED_COOLDOWN_SECONDS
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return DEFAULT_BLOCKED_COOLDOWN_SECONDS
        seconds = parsed.timestamp() - now
        return (
            max(0.0, seconds)
            if math.isfinite(seconds)
            else DEFAULT_BLOCKED_COOLDOWN_SECONDS
        )
    except (TypeError, ValueError, IndexError, OverflowError):
        return DEFAULT_BLOCKED_COOLDOWN_SECONDS


class _OwnedOperationLock(asyncio.Lock):
    """Retain operation generation even when a consumer keeps only its lock."""

    def __init__(self, state: ProviderOperationState) -> None:
        super().__init__()
        self._operation_state = state


@dataclass
class ProviderOperationState:
    """One shared operation/publication sequence, retained by active consumers."""

    generation: int = 0
    lock: asyncio.Lock = field(init=False)
    publication_lock: asyncio.Lock = field(init=False)

    def __post_init__(self) -> None:
        self.lock = _OwnedOperationLock(self)
        self.publication_lock = _OwnedOperationLock(self)


class ProviderRequestGate:
    """Serialize individual origin requests and fail fast during provider blocks.

    A single gate covers every account/entry using the Verisure origin in one
    event loop. It stores no account, credential, installation or request data.
    The HTTP lock is released before a caller sleeps between polls. Operation
    states are separate and weakly retained, so they can span such polls without
    holding the HTTP admission lock.
    """

    def __init__(
        self,
        *,
        monotonic: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], float] = time.time,
    ) -> None:
        self._clock = monotonic
        self._wall_clock = wall_clock
        self._blocked_until = 0.0
        self._request_lock = asyncio.Lock()
        self._operation_states: weakref.WeakValueDictionary[
            str, ProviderOperationState
        ] = weakref.WeakValueDictionary()

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self._blocked_until - self._clock())

    @property
    def is_blocked(self) -> bool:
        return self.remaining_seconds > 0

    def record_blocked(self, retry_after: object = None) -> float:
        """Extend shared admission cooldown; never schedule or retry a request."""
        seconds = retry_after_seconds(retry_after, self._wall_clock())
        self._blocked_until = max(self._blocked_until, self._clock() + seconds)
        return seconds

    def _ensure_available(self, session_manager: object | None) -> None:
        legacy_check = getattr(session_manager, "is_service_blocked", None)
        legacy_blocked = legacy_check() if callable(legacy_check) else legacy_check
        if self.is_blocked or legacy_blocked is True:
            raise MyVerisureServiceBlockedError(
                "Service temporarily blocked; requests are paused"
            )

    @asynccontextmanager
    async def async_request(
        self,
        session_manager: object | None = None,
    ) -> AsyncIterator[None]:
        """Check before waiting and again before any HTTP session is created."""
        self._ensure_available(session_manager)
        async with self._request_lock:
            self._ensure_available(session_manager)
            yield

    def get_operation_state(self, namespace: str) -> ProviderOperationState:
        """Resolve a shared operation state without retaining an identifying key."""
        if not isinstance(namespace, str) or not 0 < len(namespace) <= 2048:
            raise ValueError("Operation namespace must be a bounded nonempty string")
        key = hashlib.sha256(namespace.encode()).hexdigest()
        state = self._operation_states.get(key)
        if state is None:
            state = ProviderOperationState()
            self._operation_states[key] = state
        return state

    def get_operation_lock(self, namespace: str) -> asyncio.Lock:
        return self.get_operation_state(namespace).lock


def get_provider_request_gate() -> ProviderRequestGate:
    """Own provider state on the current loop, never in a process-wide registry."""
    loop = asyncio.get_running_loop()
    gate = getattr(loop, _LOOP_GATE_ATTRIBUTE, None)
    if not isinstance(gate, ProviderRequestGate):
        gate = ProviderRequestGate()
        setattr(loop, _LOOP_GATE_ATTRIBUTE, gate)
    return gate

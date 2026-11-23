"""Finite read-only background work with coalescing and a shared start budget.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import asyncio
import time
from collections import Counter, OrderedDict
from collections.abc import Awaitable, Callable

from .notifications import NotificationNotice


class BackgroundReadBudget:
    """Serialize background starts across entries without owning an HTTP lock."""

    def __init__(
        self,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._clock, self._sleep = clock, sleep
        self._next: float | None = None
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            delay = self._next - self._clock() if self._next is not None else 0
            if delay > 0:
                await self._sleep(delay)
            self._next = self._clock() + 30


class NotificationRefreshScheduler:
    """Latest hint per resource; notices can only invoke the supplied read port."""

    def __init__(
        self,
        verify: Callable[[NotificationNotice], Awaitable[bool]],
        *,
        budget: BackgroundReadBudget,
        state_enabled: bool = False,
        external_photos: bool = False,
        blocked_for: Callable[[], float] = lambda: 0,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._verify, self._budget, self._blocked_for, self._sleep = (
            verify,
            budget,
            blocked_for,
            sleep,
        )
        self._state_enabled, self._external_photos = state_enabled, external_photos
        self._pending: OrderedDict[str, NotificationNotice] = OrderedDict()
        self._counts: Counter[str] = Counter(
            dict.fromkeys(("coalesced", "overflow", "started", "failed", "deferred"), 0)
        )
        self._worker: asyncio.Task[None] | None = None
        self._closed = False

    def _resource(self, notice: NotificationNotice) -> str | None:
        event = notice.event
        if event.scope != "installation":
            return None
        if event.delivery == "reconciled":
            return "alarm" if self._state_enabled else None
        if event.delivery != "live" or event.freshness == "stale":
            return None
        if self._state_enabled:
            if event.kind in {
                "alarm_operation_reported",
                "arm_reminder",
                "unprotected_home",
                "smart_disarm_notice",
            }:
                return "alarm"
            if event.provider_request == "SMARTNOT" and notice.signal_id:
                return "incident:" + notice.signal_id
        if (
            self._external_photos
            and event.kind == "photo_reported"
            and notice.signal_id
            and notice.photo_type == 0
            and event.freshness == "fresh"
        ):
            return "photo:" + notice.signal_id
        return None

    def submit(self, notice: NotificationNotice) -> None:
        if self._closed or (key := self._resource(notice)) is None:
            return
        if key in self._pending:
            self._counts["coalesced"] += 1
        elif len(self._pending) >= 32:
            self._counts["overflow"] += 1
            return
        self._pending[key] = notice
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(
                self._run(), name="my_verisure_notification_reads"
            )

    async def _run(self) -> None:
        while self._pending and not self._closed:
            await self._sleep(2)
            while (delay := self._blocked_for()) > 0:
                await self._sleep(delay)
            await self._budget.acquire()
            # A different entry may have learned about a block while we waited.
            if self._blocked_for() > 0:
                continue
            key, notice = self._pending.popitem(last=False)
            consumed = True
            try:
                self._counts["started"] += 1
                consumed = await self._verify(notice)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Do not store exception messages; they can contain provider data.
                self._counts["failed"] += 1
                consumed = self._blocked_for() <= 0
            if not consumed:
                self._counts["deferred"] += 1
                if key not in self._pending:
                    self._pending[key] = notice

    def diagnostics(self) -> dict[str, int]:
        return {**self._counts, "pending": len(self._pending)}

    async def async_close(self) -> None:
        self._closed = True
        if self._worker is not None and not self._worker.done():
            self._worker.cancel()
            await asyncio.gather(self._worker, return_exceptions=True)
        self._pending.clear()

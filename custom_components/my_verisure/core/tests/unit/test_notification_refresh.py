"""Background hints coalesce without replaying mutations or bypassing cooldown.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api.notification_mapper import (
    NotificationMapper,
)
from custom_components.my_verisure.core.application.notification_refresh import (
    BackgroundReadBudget,
    NotificationRefreshScheduler,
)
from .test_notification_admission import envelope, NOW


class Clock:
    def __init__(self):
        self.now = 0.0
        self.waits = []

    async def sleep(self, seconds):
        self.waits.append(seconds)
        self.now += seconds
        await asyncio.sleep(0)


def notice(kind="ARMDISARM", signal="123", delivery="one"):
    return NotificationMapper("house", "entry")(
        envelope(kind, idSignal=signal), delivery, NOW
    ).notice


async def settle(predicate):
    for _ in range(100):
        if predicate():
            return
        await asyncio.sleep(0)
    assert predicate()


@pytest.mark.asyncio
async def test_burst_keeps_latest_one_resource_and_unknown_does_no_work():
    clock, seen = Clock(), []

    async def verify(value):
        seen.append(value)
        return True

    scheduler = NotificationRefreshScheduler(
        verify,
        budget=BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep),
        sleep=clock.sleep,
        state_enabled=True,
    )
    for n in range(50):
        scheduler.submit(notice(delivery=str(n)))
    scheduler.submit(notice("NOT"))
    await settle(lambda: len(seen) == 1)
    assert seen[0].event == notice(delivery="49").event
    assert scheduler.diagnostics()["coalesced"] == 49
    assert clock.waits[0] == 2
    await scheduler.async_close()


@pytest.mark.asyncio
async def test_shared_budget_spaces_reads_between_entries_and_retries_dirty_once():
    clock = Clock()
    budget = BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep)
    verify = AsyncMock(side_effect=[False, True, True])
    first = NotificationRefreshScheduler(
        verify, budget=budget, sleep=clock.sleep, state_enabled=True
    )
    second = NotificationRefreshScheduler(
        verify, budget=budget, sleep=clock.sleep, state_enabled=True
    )
    first.submit(notice())
    second.submit(notice())
    await settle(lambda: verify.await_count == 3)
    assert sum(value >= 26 for value in clock.waits) >= 2
    assert first.diagnostics()["deferred"] + second.diagnostics()["deferred"] == 1
    await first.async_close()
    await second.async_close()


@pytest.mark.asyncio
async def test_queue_is_bounded_and_external_photo_is_explicit_opt_in():
    # A real blocked sleeper lets us inspect the queue before it is consumed.
    async def pause(_):
        await asyncio.Event().wait()

    verify = AsyncMock(return_value=True)
    off = NotificationRefreshScheduler(
        verify, budget=BackgroundReadBudget(), sleep=pause
    )
    off.submit(notice("INF"))
    off.submit(notice())
    assert off.diagnostics()["pending"] == 0
    on = NotificationRefreshScheduler(
        verify, budget=BackgroundReadBudget(), sleep=pause, external_photos=True
    )
    for n in range(40):
        on.submit(notice("INF", str(n)))
    assert on.diagnostics()["pending"] == 32
    assert on.diagnostics()["overflow"] == 8
    await on.async_close()
    on.submit(notice("INF"))
    assert on.diagnostics()["pending"] == 0
    verify.assert_not_awaited()
    await off.async_close()


@pytest.mark.asyncio
async def test_provider_block_retains_hint_and_permanent_failure_does_not_loop():
    clock, attempts = Clock(), []
    blocked = [14.0]

    async def verify(value):
        attempts.append(value)
        if len(attempts) == 1:
            blocked[0] = clock.now + 600.0
            raise RuntimeError("synthetic private provider detail")
        blocked[0] = 0
        return True

    async def sleep(seconds):
        await clock.sleep(seconds)

    scheduler = NotificationRefreshScheduler(
        verify,
        budget=BackgroundReadBudget(clock=lambda: clock.now, sleep=sleep),
        sleep=sleep,
        state_enabled=True,
        blocked_for=lambda: max(0, blocked[0] - clock.now),
    )
    scheduler.submit(notice())
    await settle(lambda: len(attempts) == 2)
    assert 598 in clock.waits and 12 in clock.waits
    assert scheduler.diagnostics()["failed"] == 1
    await scheduler.async_close()
    bad = NotificationRefreshScheduler(
        AsyncMock(side_effect=ValueError()),
        budget=BackgroundReadBudget(clock=lambda: clock.now, sleep=sleep),
        sleep=sleep,
        state_enabled=True,
    )
    bad.submit(notice())
    await settle(lambda: bad.diagnostics()["failed"] == 1)
    assert bad.diagnostics()["pending"] == 0
    await bad.async_close()


@pytest.mark.asyncio
async def test_stale_foreign_unknown_and_incident_without_reference_are_not_scheduled():
    from dataclasses import replace

    verify = AsyncMock(return_value=True)
    scheduler = NotificationRefreshScheduler(
        verify, budget=BackgroundReadBudget(), state_enabled=True
    )
    value = notice()
    for changes in (
        {"scope": "account"},
        {"freshness": "stale"},
        {"delivery": "restored"},
    ):
        scheduler.submit(replace(value, event=replace(value.event, **changes)))
    scheduler.submit(notice("ALARMTRIGGER"))
    scheduler.submit(notice("FUTURE_PROVIDER_TYPE"))
    assert scheduler.diagnostics()["pending"] == 0
    await scheduler.async_close()

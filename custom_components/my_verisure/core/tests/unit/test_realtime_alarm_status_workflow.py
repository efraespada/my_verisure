"""Tests for realtime alarm status workflow."""

from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.application.realtime_alarm_status_workflow import (
    RealtimeAlarmStatusWorkflow,
)


@pytest.mark.asyncio
async def test_workflow_returns_success_without_waiting():
    transport = AsyncMock(
        return_value={"data": {"xSCheckAlarmStatus": {"res": "OK", "msg": "armed"}}}
    )
    sleep = AsyncMock()

    result = await RealtimeAlarmStatusWorkflow(sleep=sleep).run(transport)

    assert result == "armed"
    transport.assert_awaited_once_with(0)
    sleep.assert_not_awaited()


@pytest.mark.asyncio
async def test_workflow_retries_wait_then_returns_success():
    transport = AsyncMock(
        side_effect=[
            {"data": {"xSCheckAlarmStatus": {"res": "WAIT", "msg": "pending"}}},
            {"data": {"xSCheckAlarmStatus": {"res": "OK", "msg": "armed"}}},
        ]
    )
    sleep = AsyncMock()

    result = await RealtimeAlarmStatusWorkflow(
        max_retries=2, retry_delay_seconds=0.25, sleep=sleep
    ).run(transport)

    assert result == "armed"
    assert transport.await_count == 2
    sleep.assert_awaited_once_with(0.25)


@pytest.mark.asyncio
async def test_workflow_returns_empty_after_wait_exhaustion():
    transport = AsyncMock(
        return_value={"data": {"xSCheckAlarmStatus": {"res": "WAIT", "msg": "pending"}}}
    )
    sleep = AsyncMock()

    result = await RealtimeAlarmStatusWorkflow(max_retries=3, sleep=sleep).run(transport)

    assert result == ""
    assert transport.await_count == 3
    assert sleep.await_count == 2


@pytest.mark.asyncio
async def test_workflow_converts_transport_failure_to_empty_message():
    transport = AsyncMock(side_effect=RuntimeError("offline"))

    assert await RealtimeAlarmStatusWorkflow().run(transport) == ""


@pytest.mark.parametrize(
    ("max_retries", "retry_delay_seconds"),
    [(0, 1), (1, -1)],
)
def test_workflow_rejects_invalid_policy(max_retries, retry_delay_seconds):
    with pytest.raises(ValueError):
        RealtimeAlarmStatusWorkflow(
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
        )

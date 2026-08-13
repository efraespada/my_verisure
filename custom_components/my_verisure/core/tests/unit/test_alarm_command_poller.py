"""Tests for the application-level alarm command poller."""

from collections.abc import Mapping

import pytest

from custom_components.my_verisure.core.application.alarm_command_poller import (
    AlarmCommandPoller,
)


@pytest.mark.asyncio
async def test_poll_arm_waits_then_returns_success() -> None:
    responses: list[Mapping[str, object]] = [
        {"data": {"xSArmStatus": {"res": "WAIT", "msg": "processing"}}},
        {"data": {"xSArmStatus": {"res": "OK", "msg": "armed"}}},
    ]

    async def transport(attempt: int) -> Mapping[str, object]:
        return responses[attempt - 1]

    result = await AlarmCommandPoller(max_retries=2, retry_delay=0).poll_arm(
        transport,
        reference_id="ref-1",
    )

    assert result.success is True
    assert result.message == "armed"
    assert result.reference_id == "ref-1"


@pytest.mark.asyncio
async def test_poll_disarm_returns_graphql_error() -> None:
    async def transport(_: int) -> Mapping[str, object]:
        return {"errors": [{"message": "upstream failure"}]}

    result = await AlarmCommandPoller(max_retries=3, retry_delay=0).poll_disarm(
        transport,
        reference_id="ref-2",
    )

    assert result.success is False
    assert result.message == "upstream failure"
    assert result.reference_id == "ref-2"


@pytest.mark.asyncio
async def test_poll_arm_returns_exhaustion_result() -> None:
    async def transport(_: int) -> Mapping[str, object]:
        return {"data": {"xSArmStatus": {"res": "WAIT", "msg": "processing"}}}

    result = await AlarmCommandPoller(max_retries=2, retry_delay=0).poll_arm(
        transport,
        reference_id="ref-3",
    )

    assert result.success is False
    assert result.message == "Alarm command polling exhausted"


@pytest.mark.asyncio
async def test_poll_disarm_returns_unknown_response_as_failure() -> None:
    async def transport(_: int) -> Mapping[str, object]:
        return {"data": {"xSDisarmStatus": {"res": "UNKNOWN", "msg": "unexpected"}}}

    result = await AlarmCommandPoller(max_retries=2, retry_delay=0).poll_disarm(
        transport,
        reference_id="ref-4",
    )

    assert result.success is False
    assert result.message == "unexpected"

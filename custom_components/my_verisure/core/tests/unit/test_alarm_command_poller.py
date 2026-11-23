"""Tests for the application-level alarm command poller."""

from collections.abc import Mapping
from unittest.mock import AsyncMock, call, patch

import pytest

from custom_components.my_verisure.core.api.alarm_command_poller import (
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
    assert result.message == "Alarm command accepted"
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
    assert result.message == "Alarm service request failed"
    assert result.reference_id == "ref-2"


@pytest.mark.asyncio
async def test_poll_arm_rejects_empty_graphql_errors() -> None:
    async def transport(_: int) -> Mapping[str, object]:
        return {"errors": []}

    result = await AlarmCommandPoller(max_retries=1, retry_delay=0).poll_arm(
        transport, reference_id="ref-empty"
    )

    assert result.success is False
    assert result.message == "Alarm service request failed"


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
    assert result.message == "Disarm command rejected"


@pytest.mark.asyncio
async def test_default_command_polling_matches_native_one_second_cadence():
    transport = AsyncMock(return_value={"data": {"xSArmStatus": {"res": "WAIT"}}})
    with patch(
        "custom_components.my_verisure.core.api.alarm_command_poller.asyncio.sleep",
        new_callable=AsyncMock,
    ) as sleep:
        result = await AlarmCommandPoller(max_retries=6).poll_arm(
            transport, reference_id="synthetic-reference"
        )

    assert result.success is False
    assert transport.await_count == 6
    assert sleep.await_args_list == [call(1)] * 5


@pytest.mark.parametrize("operation,payload_key,code", [("poll_arm", "xSArmStatus", "E"), ("poll_disarm", "xSDisarmStatus", "D")])
async def test_command_completion_retains_provider_confirmed_panel_state(operation, payload_key, code):
    transport = AsyncMock(return_value={"data": {payload_key: {"res": "OK", "protomResponse": code}}})

    result = await getattr(AlarmCommandPoller(), operation)(transport, reference_id="ref")

    assert result.confirmed_state == code

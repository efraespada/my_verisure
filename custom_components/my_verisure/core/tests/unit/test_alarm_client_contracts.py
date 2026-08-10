"""Alarm client response contract tests."""

from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient


@pytest.mark.asyncio
async def test_realtime_status_returns_empty_message_for_graphql_error():
    client = AlarmClient()
    client._execute_alarm_status_check_direct = AsyncMock(
        return_value={"errors": [{"message": "upstream failure"}]}
    )

    result = await client._get_real_time_alarm_status(
        numinst="1",
        panel="panel",
        id_service="EST",
        reference_id="ref",
        capabilities="caps",
    )

    assert result == ""


@pytest.mark.asyncio
async def test_realtime_status_returns_empty_message_for_unknown_response():
    client = AlarmClient()
    client._execute_alarm_status_check_direct = AsyncMock(
        return_value={
            "data": {
                "xSCheckAlarmStatus": {"res": "UNKNOWN", "msg": "unexpected"}
            }
        }
    )

    result = await client._get_real_time_alarm_status(
        numinst="1",
        panel="panel",
        id_service="EST",
        reference_id="ref",
        capabilities="caps",
    )

    assert result == ""

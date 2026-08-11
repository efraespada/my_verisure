"""Alarm client response contract tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient


@pytest.mark.asyncio
async def test_alarm_status_configuration_cache_is_instance_scoped():
    first = AlarmClient()
    second = AlarmClient()
    first._read_alarm_status_file = Mock(return_value={"owner": "first"})
    second._read_alarm_status_file = Mock(return_value={"owner": "second"})

    first_config = await first._load_alarm_status_config()
    second_config = await second._load_alarm_status_config()

    assert first_config == {"owner": "first"}
    assert second_config == {"owner": "second"}
    assert first_config is not second_config


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

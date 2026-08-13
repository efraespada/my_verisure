"""Alarm client response contract tests."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def _alarm_client(tmp_path):
    file_manager = FileManager(tmp_path)
    session_manager = SessionManager(file_manager=file_manager)
    return AlarmClient(session_manager=session_manager)


@pytest.mark.asyncio
async def test_alarm_status_configuration_cache_is_instance_scoped(tmp_path):
    first = _alarm_client(tmp_path / "first")
    second = _alarm_client(tmp_path / "second")
    first._read_alarm_status_file = Mock(return_value={"owner": "first"})
    second._read_alarm_status_file = Mock(return_value={"owner": "second"})

    first_config = await first._load_alarm_status_config()
    second_config = await second._load_alarm_status_config()

    assert first_config == {"owner": "first"}
    assert second_config == {"owner": "second"}
    assert first_config is not second_config


@pytest.mark.asyncio
async def test_realtime_status_returns_empty_message_for_graphql_error(tmp_path):
    client = _alarm_client(tmp_path)
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
async def test_realtime_status_returns_empty_message_for_unknown_response(tmp_path):
    client = _alarm_client(tmp_path)
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


@pytest.mark.asyncio
async def test_send_alarm_command_converts_transport_exception_to_failed_result(
    tmp_path,
) -> None:
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("hash", {"user": "user"}))
    client._execute_arm_panel_direct = AsyncMock(side_effect=RuntimeError("offline"))

    result = await client.send_alarm_command("1", "panel", "ARM1", capabilities="caps")

    assert result.success is False
    assert result.message == "Unexpected error: offline"

"""Read spontaneous-notification state without initiating panel radio checks.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient
from custom_components.my_verisure.core.api.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.alarm_status_service import (
    AlarmStatusService,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.parametrize("code", ["D", "E", "Q", "C", "unmapped-provider-mode"])
async def test_native_current_status_reader_maps_or_preserves_unknown_without_radio(
    tmp_path, code
):
    client = AlarmClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(
        return_value=("synthetic-session", {"user": "synthetic"})
    )
    client._execute_query_direct = AsyncMock(
        return_value={"data": {"xSStatus": {"status": code}}}
    )
    client._execute_check_alarm_direct = AsyncMock(
        side_effect=AssertionError("no radio mutation")
    )
    result = await client.get_current_alarm_status(
        "synthetic-house", "synthetic-panel", "synthetic-caps"
    )
    assert result == AlarmStatusService.from_panel_code(code)
    assert client._execute_query_direct.await_count == 1
    assert "query Status" in client._execute_query_direct.await_args.args[0]
    client._execute_check_alarm_direct.assert_not_awaited()


@pytest.mark.parametrize(
    "payload", [{}, {"data": None}, {"data": {"xSStatus": {"status": None}}}]
)
async def test_native_current_status_reader_fails_on_missing_response_without_radio(
    tmp_path, payload
):
    client = AlarmClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(
        return_value=("synthetic-session", {"user": "synthetic"})
    )
    client._execute_query_direct = AsyncMock(return_value=payload)
    client._execute_check_alarm_direct = AsyncMock(
        side_effect=AssertionError("no radio mutation")
    )
    with pytest.raises(MyVerisureError):
        await client.get_current_alarm_status(
            "synthetic-house", "synthetic-panel", "synthetic-caps"
        )
    client._execute_check_alarm_direct.assert_not_awaited()

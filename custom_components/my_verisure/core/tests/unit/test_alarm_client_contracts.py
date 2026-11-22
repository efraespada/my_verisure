"""Alarm client response contract tests."""
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureError,
)
from custom_components.my_verisure.core.application.alarm_status_service import AlarmStatusService
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def _alarm_client(tmp_path):
    file_manager = FileManager(tmp_path)
    session_manager = SessionManager(file_manager=file_manager)
    return AlarmClient(session_manager=session_manager)


@pytest.mark.asyncio
async def test_alarm_status_configuration_cache_is_instance_scoped(tmp_path):
    first = AlarmStatusService(
        tmp_path / "first.json", read_config=lambda _: {"owner": "first"}
    )
    second = AlarmStatusService(
        tmp_path / "second.json", read_config=lambda _: {"owner": "second"}
    )

    first_config = await first.load_config()
    second_config = await second.load_config()

    assert first_config == {"owner": "first"}
    assert second_config == {"owner": "second"}
    assert first_config is not second_config


@pytest.mark.asyncio
async def test_realtime_status_rejects_graphql_error(tmp_path):
    client = _alarm_client(tmp_path)
    client._execute_alarm_status_check_direct = AsyncMock(
        return_value={"errors": [{"message": "upstream failure"}]}
    )

    with pytest.raises(MyVerisureError, match="realtime alarm status response"):
        await client._get_real_time_alarm_status(
            numinst="1",
            panel="panel",
            id_service="EST",
            reference_id="ref",
            capabilities="caps",
        )


@pytest.mark.asyncio
async def test_realtime_status_propagates_provider_error(tmp_path):
    client = _alarm_client(tmp_path)
    client._execute_alarm_status_check_direct = AsyncMock(
        side_effect=MyVerisureError("provider failure")
    )

    with pytest.raises(MyVerisureError, match="provider failure"):
        await client._get_real_time_alarm_status(
            numinst="1",
            panel="panel",
            id_service="EST",
            reference_id="ref",
            capabilities="caps",
        )


@pytest.mark.asyncio
async def test_realtime_status_rejects_unknown_response(tmp_path):
    client = _alarm_client(tmp_path)
    client._execute_alarm_status_check_direct = AsyncMock(
        return_value={
            "data": {
                "xSCheckAlarmStatus": {"res": "UNKNOWN", "msg": "unexpected"}
            }
        }
    )

    with pytest.raises(MyVerisureError, match="realtime alarm status response"):
        await client._get_real_time_alarm_status(
            numinst="1",
            panel="panel",
            id_service="EST",
            reference_id="ref",
            capabilities="caps",
        )


@pytest.mark.asyncio
async def test_get_alarm_status_requires_authentication(tmp_path):
    client = _alarm_client(tmp_path)

    with pytest.raises(MyVerisureAuthenticationError, match="Not authenticated"):
        await client.get_alarm_status("1", "panel", "caps")


@pytest.mark.asyncio
async def test_get_alarm_status_rejects_empty_graphql_errors(tmp_path):
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("hash", {"user": "user"}))
    client._execute_alarm_graphql = AsyncMock(return_value={"data": {"xSStatus": {"status": "UNRECOGNIZED"}}})
    client._execute_check_alarm_direct = AsyncMock(return_value={"errors": []})

    with pytest.raises(MyVerisureError, match="Failed to get alarm status"):
        await client.get_alarm_status("1", "panel", "caps")


@pytest.mark.asyncio
async def test_get_alarm_status_rejects_incomplete_check_alarm(tmp_path):
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("hash", {"user": "user"}))
    client._execute_alarm_graphql = AsyncMock(return_value={"data": {"xSStatus": {"status": "UNRECOGNIZED"}}})
    client._execute_check_alarm_direct = AsyncMock(return_value={"data": {}})

    with pytest.raises(MyVerisureError, match="alarm status"):
        await client.get_alarm_status("1", "panel", "caps")


@pytest.mark.asyncio
async def test_realtime_status_rejects_transport_failure(tmp_path):
    client = _alarm_client(tmp_path)
    client._execute_alarm_status_check_direct = AsyncMock(
        side_effect=RuntimeError("offline")
    )

    with pytest.raises(MyVerisureError, match="realtime alarm status transport failed"):
        await client._get_real_time_alarm_status(
            numinst="1",
            panel="panel",
            id_service="EST",
            reference_id="ref",
            capabilities="caps",
        )


@pytest.mark.asyncio
async def test_send_alarm_command_converts_transport_exception_to_failed_result(
    tmp_path,
) -> None:
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("hash", {"user": "user"}))
    client._execute_arm_panel_direct = AsyncMock(side_effect=RuntimeError("offline"))
    client._execute_alarm_graphql = AsyncMock(return_value={"data": {"xSStatus": {"status": "D"}}})

    result = await client.send_alarm_command("1", "panel", "ARM1", capabilities="caps")

    assert result.success is False
    assert result.message == "Alarm command failed"

@pytest.mark.asyncio
async def test_send_alarm_command_propagates_domain_error(tmp_path) -> None:
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("hash", {"user": "user"}))
    client._execute_arm_panel_direct = AsyncMock(
        side_effect=MyVerisureError("domain failure")
    )
    client._execute_alarm_graphql = AsyncMock(return_value={"data": {"xSStatus": {"status": "D"}}})

    with pytest.raises(MyVerisureError, match="domain failure"):
        await client.send_alarm_command("1", "panel", "ARM1", capabilities="caps")


@pytest.mark.asyncio
async def test_arm_home_uses_provider_current_status_instead_of_fixed_default(tmp_path):
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("synthetic-token", {"user": "synthetic-user"}))
    calls = []

    async def provider(query, variables=None, headers=None):
        calls.append((query, variables))
        if "query Status" in query:
            return {"data": {"xSStatus": {"status": "D"}}}
        if "mutation xSArmPanel" in query:
            return {"data": {"xSArmPanel": {"res": "OK", "referenceId": "synthetic-reference"}}}
        return {"data": {"xSArmStatus": {"res": "OK"}}}

    client._execute_query_direct = provider

    assert (await client.arm_alarm_home("synthetic-installation", "SYNTHETIC", "synthetic-capabilities")).success
    assert "query Status" in calls[0][0]
    assert calls[1][1]["currentStatus"] == "D"
    assert calls[1][1]["request"] == "PERI1"


@pytest.mark.asyncio
@pytest.mark.parametrize("reply", [
    {"data": {"xSStatus": {"status": None}}},
    {"data": {"xSStatus": {"status": ""}}},
    {},
    {"errors": [{"message": "expired"}], "data": {"xSStatus": {"status": "D"}}},
])
async def test_arm_command_requires_unambiguous_current_panel_status(tmp_path, reply):
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("synthetic-token", {"user": "synthetic-user"}))
    client._execute_alarm_graphql = AsyncMock(return_value=reply)
    client._execute_arm_panel_direct = AsyncMock()

    with pytest.raises(MyVerisureError, match="Current panel status unavailable"):
        await client.arm_alarm_home("synthetic-installation", "SYNTHETIC", "synthetic-capabilities")

    client._execute_arm_panel_direct.assert_not_awaited()


@pytest.mark.parametrize("code,external,night", [("D", False, False), ("E", True, False), ("Q", False, True), ("C", True, True)])
async def test_native_status_read_avoids_redundant_panel_radio_check(tmp_path, code, external, night):
    client = _alarm_client(tmp_path)
    client._get_current_credentials = Mock(return_value=("hash", {"user": "user"}))
    client._execute_query_direct = AsyncMock(return_value={"data": {"xSStatus": {"status": code}}})
    client._execute_check_alarm_direct = AsyncMock(side_effect=AssertionError("unnecessary radio request"))

    status = await client.get_alarm_status("installation", "panel", "caps")

    assert status["external"]["status"] is external
    assert status["internal"]["total"]["status"] is False
    assert status["internal"]["night"]["status"] is night
    assert client._execute_query_direct.await_count == 1
    client._execute_check_alarm_direct.assert_not_awaited()

"""Tests for the alarm GraphQL transport boundary."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def _client(tmp_path):
    return AlarmClient(
        session_manager=SessionManager(file_manager=FileManager(tmp_path))
    )


@pytest.mark.asyncio
async def test_alarm_graphql_transport_adds_entry_scoped_headers(tmp_path):
    client = _client(tmp_path)
    client._get_session_headers = Mock(return_value={"auth": "redacted"})
    client._execute_query_direct = AsyncMock(return_value={"data": {"ok": True}})

    result = await client._execute_alarm_graphql(
        "AlarmOperation",
        "query AlarmOperation { ok }",
        {"numinst": "home-1"},
        "home-1",
        "panel-1",
        "capability-1",
        "hash-1",
        {"user": "user@example.invalid"},
    )

    assert result == {"data": {"ok": True}}
    client._execute_query_direct.assert_awaited_once()
    call = client._execute_query_direct.await_args
    assert call is not None
    headers = call.args[2]
    assert headers == {
        "auth": "redacted",
        "numinst": "home-1",
        "panel": "panel-1",
        "x-capabilities": "capability-1",
    }


@pytest.mark.asyncio
async def test_alarm_graphql_transport_returns_redacted_error_payload(tmp_path):
    client = _client(tmp_path)
    client._execute_query_direct = AsyncMock(side_effect=TimeoutError("offline"))

    result = await client._execute_alarm_graphql(
        "AlarmOperation",
        "query AlarmOperation { ok }",
        {},
        "home-1",
        "panel-1",
        "capability-1",
    )

    assert result == {"errors": [{"message": "offline", "data": {}}]}

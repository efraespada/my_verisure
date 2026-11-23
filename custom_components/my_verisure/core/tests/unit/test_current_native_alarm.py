"""Replay the observed native partial-night and optional-perimeter contract.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from unittest.mock import Mock

import pytest

from custom_components.my_verisure.core.api.alarm_client import AlarmClient
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager
from custom_components.my_verisure.core.repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl


@pytest.mark.parametrize("perimeter,expected_requests,expected_state", [(False, ["ARMNIGHT1"], "Q"), (True, ["ARMNIGHT1", "PERI1"], "C")])
async def test_night_mapping_matches_native_with_configurable_perimeter(tmp_path, perimeter, expected_requests, expected_state):
    client = AlarmClient(SessionManager(file_manager=FileManager(tmp_path)))
    client._get_current_credentials = Mock(return_value=("synthetic-token", {"user": "synthetic-user"}))
    requests = []
    current_states = []
    state = "D"

    async def provider(query, variables=None, headers=None):
        nonlocal state
        if "query Status" in query:
            return {"data": {"xSStatus": {"status": state}}}
        if "mutation xSArmPanel" in query:
            requests.append(variables["request"])
            current_states.append(variables["currentStatus"])
            return {"data": {"xSArmPanel": {"res": "OK", "referenceId": "synthetic-ref"}}}
        state = "Q" if variables["request"] == "ARMNIGHT1" else "C"
        return {"data": {"xSArmStatus": {"res": "OK", "protomResponse": state}}}

    client._execute_query_direct = provider
    result = await AlarmRepositoryImpl(client).arm_night("synthetic-installation", "panel", "caps", perimeter)

    assert result.success
    assert result.confirmed_state == expected_state
    assert requests == expected_requests
    assert current_states == (["D", "Q"] if perimeter else ["D"])

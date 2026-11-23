"""Explicitly changed credentials require a provider password login.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api.auth_client import AuthClient
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.application.auth_session_persistence import (
    AuthSessionPersistence,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.repositories.implementations import (
    auth_repository_impl,
)
from custom_components.my_verisure.core.session_manager import SessionManager
from custom_components.my_verisure.core.use_cases.implementations import (
    auth_use_case_impl,
)


def _success(field):
    return {
        "data": {
            field: {
                "res": "OK",
                "msg": "auth-api.login.success",
                "hash": "fixture-new-hash",
                "refreshToken": "fixture-new-refresh",
                "needDeviceAuthorization": False,
            }
        }
    }


@pytest.mark.parametrize("prior_password", [None, "fixture-old-password"])
@pytest.mark.asyncio
async def test_changed_or_unbound_password_bypasses_existing_refresh(
    tmp_path, prior_password
):
    files = FileManager(tmp_path)
    session = SessionManager(file_manager=files)
    session.username = "fixture-user"
    session.password = prior_password
    session.refresh_token = "fixture-existing-refresh"
    client = AuthClient(session, DeviceManager(files))

    async def query(query, variables, headers):
        return _success(
            "xSRefreshLogin" if "refreshToken" in variables else "xSLoginToken"
        )

    client._execute_query_direct = AsyncMock(side_effect=query)

    result = await client.login("fixture-user", "fixture-new-password")

    assert result.hash == "fixture-new-hash"
    client._execute_query_direct.assert_awaited_once()
    variables = client._execute_query_direct.await_args.args[1]
    assert variables["password"] == "fixture-new-password"
    assert "refreshToken" not in variables


@pytest.mark.asyncio
async def test_rejected_new_password_preserves_previous_session_and_disk(tmp_path):
    files = FileManager(tmp_path)
    session = SessionManager(file_manager=files)
    await session.async_update_credentials(
        "fixture-user",
        "fixture-old-password",
        "fixture-old-hash",
        "fixture-old-refresh",
    )
    previous_memory = session.capture_transaction_state()
    previous_bytes = Path(session.session_file).read_bytes()
    client = AuthClient(session, DeviceManager(files))

    async def query(query, variables, headers):
        if "refreshToken" in variables:
            return _success("xSRefreshLogin")
        return {
            "errors": [{"message": "Invalid credentials", "data": {"err": "60091"}}]
        }

    client._execute_query_direct = AsyncMock(side_effect=query)
    use_case = auth_use_case_impl.AuthUseCaseImpl(
        auth_repository_impl.AuthRepositoryImpl(client), AuthSessionPersistence(session)
    )

    result = await use_case.login("fixture-user", "fixture-invalid-password")

    assert result.success is False
    assert session.capture_transaction_state() == previous_memory
    assert Path(session.session_file).read_bytes() == previous_bytes
    client._execute_query_direct.assert_awaited_once()

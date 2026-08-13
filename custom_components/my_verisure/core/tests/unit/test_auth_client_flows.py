"""Characterization tests for AuthClient protocol branches."""

import json
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.auth_client import AuthClient
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureOTPError,
)
from custom_components.my_verisure.core.api.models.dto.auth_dto import AuthDTO
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.fixture
def client(tmp_path) -> AuthClient:
    file_manager = FileManager(tmp_path)
    session_manager = SessionManager(file_manager=file_manager)
    setattr(session_manager, "async_update_credentials", AsyncMock())
    setattr(session_manager, "clear_service_blocked", Mock())
    device_manager = Mock()
    device_manager.async_ensure_device_identifiers = AsyncMock()
    device_manager.get_login_variables.return_value = {"uuid": "device-id"}
    device_manager.get_validation_variables.return_value = {"uuid": "device-id"}
    result = AuthClient(
        session_manager=session_manager,
        device_manager=device_manager,
    )
    result._session_data = {"user": "user", "lang": "ES"}
    result._hash = "session-hash"
    return result


def _set_query_result(client: AuthClient, result: dict[str, Any]) -> None:
    setattr(client, "_execute_query_direct", AsyncMock(return_value=result))


def _login_response(**overrides: Any) -> dict[str, Any]:
    data = {
        "res": "OK",
        "msg": "Login successful",
        "hash": "session-hash",
        "refreshToken": "refresh-token",
        "lang": "ES",
        "legals": False,
        "changePassword": False,
        "needDeviceAuthorization": False,
    }
    data.update(overrides)
    return {"data": {"xSLoginToken": data}}


@pytest.mark.asyncio
async def test_login_success_updates_entry_scoped_session(client: AuthClient) -> None:
    _set_query_result(client, _login_response())

    result = await client.login("user", "password")

    assert isinstance(result, AuthDTO)
    assert result.res == "OK"
    session_manager = client._resolve_session_manager()
    update_credentials = cast(AsyncMock, session_manager.async_update_credentials)
    clear_service_blocked = cast(Mock, session_manager.clear_service_blocked)
    assert update_credentials.await_args is not None
    assert update_credentials.await_args.args == (
        "user",
        "password",
        "session-hash",
        "refresh-token",
    )
    clear_service_blocked.assert_called_once_with()


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials_graphql_error(client: AuthClient) -> None:
    _set_query_result(
        client,
        {"errors": [{"message": "invalid credentials", "data": {"err": "60091"}}]},
    )

    with pytest.raises(MyVerisureAuthenticationError, match="Invalid user or password"):
        await client.login("user", "password")


@pytest.mark.asyncio
async def test_login_rejects_success_without_hash(client: AuthClient) -> None:
    _set_query_result(client, _login_response(hash=None))

    with pytest.raises(MyVerisureAuthenticationError, match="without a session hash"):
        await client.login("user", "password")

    update_credentials = cast(
        AsyncMock, client._resolve_session_manager().async_update_credentials
    )
    update_credentials.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_requires_otp_when_device_authorization_is_needed(
    client: AuthClient,
) -> None:
    _set_query_result(client, _login_response(needDeviceAuthorization=True))
    check_authorization = AsyncMock(side_effect=MyVerisureOTPError("OTP required"))
    complete_authorization = AsyncMock(side_effect=MyVerisureOTPError("OTP flow started"))
    setattr(client, "_check_device_authorization", check_authorization)
    setattr(client, "_complete_device_authorization", complete_authorization)

    with pytest.raises(MyVerisureOTPError, match="OTP flow started"):
        await client.login("user", "password")

    check_authorization.assert_awaited_once_with()
    complete_authorization.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_send_otp_returns_true_for_successful_response(client: AuthClient) -> None:
    _set_query_result(
        client,
        {"data": {"xSSendOtp": {"res": "OK", "msg": "sent"}}},
    )
    client._otp_data = {"phones": [], "otp_hash": "old-hash"}

    assert await client.send_otp(7, "otp-hash") is True
    assert client._otp_data["otp_hash"] == "otp-hash"


@pytest.mark.asyncio
async def test_send_otp_rejects_graphql_error(client: AuthClient) -> None:
    _set_query_result(client, {"errors": [{"message": "delivery failed"}]})

    with pytest.raises(MyVerisureOTPError, match="delivery failed"):
        await client.send_otp(7, "otp-hash")


@pytest.mark.asyncio
async def test_send_otp_rejects_empty_provider_payload(client: AuthClient) -> None:
    _set_query_result(client, {"data": {"xSSendOtp": {}}})

    with pytest.raises(MyVerisureOTPError, match="No response data"):
        await client.send_otp(7, "otp-hash")


@pytest.mark.asyncio
async def test_verify_otp_requires_stored_otp_data(client: AuthClient) -> None:
    with pytest.raises(MyVerisureOTPError, match="No OTP data"):
        await client.verify_otp("123456")


@pytest.mark.asyncio
async def test_verify_otp_rejects_unsuccessful_validation(client: AuthClient) -> None:
    client._otp_data = {"phones": [], "otp_hash": "otp-hash"}
    _set_query_result(
        client,
        {"data": {"xSValidateDevice": {"res": "ERROR", "msg": "invalid code"}}},
    )

    with pytest.raises(MyVerisureOTPError, match="invalid code"):
        await client.verify_otp("123456")


@pytest.mark.asyncio
async def test_verify_otp_sends_security_contract_and_refreshes_session(
    client: AuthClient,
) -> None:
    client._otp_data = {"phones": [], "otp_hash": "otp-hash"}
    _set_query_result(
        client,
        {
            "data": {
                "xSValidateDevice": {
                    "res": "OK",
                    "hash": "otp-session-hash",
                    "refreshToken": "otp-refresh-token",
                    "needDeviceAuthorization": False,
                }
            }
        },
    )
    post_otp_login = AsyncMock(
        return_value=AuthDTO(
            res="OK",
            msg="fresh session",
            hash="fresh-hash",
            refresh_token="fresh-refresh",
        )
    )
    setattr(client, "_perform_post_otp_login", post_otp_login)

    result = await client.verify_otp("123456")

    assert result.hash == "fresh-hash"
    post_otp_login.assert_awaited_once_with()
    execute_query = cast(AsyncMock, client._execute_query_direct)
    assert execute_query.await_args is not None
    request_headers = execute_query.await_args.args[2]
    security = json.loads(request_headers["Security"])
    assert security == {"token": "123456", "type": "OTP", "otpHash": "otp-hash"}

"""Characterization tests for AuthClient protocol branches."""

import asyncio
import json
import time
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from custom_components.my_verisure.core.api.auth_client import AuthClient
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureOTPError,
    MyVerisureTimeoutError,
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
    device_manager.get_login_variables.return_value = {"uuid": "[REDACTED]"}
    device_manager.get_validation_variables.return_value = {"uuid": "[REDACTED]"}
    result = AuthClient(
        session_manager=session_manager,
        device_manager=device_manager,
    )
    session_manager.username = "[REDACTED]"
    session_manager.password = "[REDACTED]"
    session_manager.hash_token = "[REDACTED]"
    result._otp_expires_at = time.monotonic() + 300
    return result


def _set_query_result(client: AuthClient, result: dict[str, Any]) -> None:
    setattr(client, "_execute_query_direct", AsyncMock(return_value=result))


def _login_response(**overrides: Any) -> dict[str, Any]:
    data = {
        "res": "OK",
        "msg": "Login successful",
        "hash": "[REDACTED]",
        "refreshToken": "[REDACTED]",
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

    result = await client.login("[REDACTED]", "[REDACTED]")

    assert isinstance(result, AuthDTO)
    assert result.res == "OK"
    session_manager = client._resolve_session_manager()
    update_credentials = cast(AsyncMock, session_manager.async_update_credentials)
    clear_service_blocked = cast(Mock, session_manager.clear_service_blocked)
    update_credentials.assert_not_awaited()
    clear_service_blocked.assert_not_called()


@pytest.mark.asyncio
async def test_login_rejects_empty_refresh_token(client: AuthClient) -> None:
    _set_query_result(client, _login_response(refreshToken=""))

    with pytest.raises(MyVerisureAuthenticationError, match="Authentication response failed"):
        await client.login("[REDACTED]", "[REDACTED]")




@pytest.mark.asyncio
async def test_login_accepts_missing_optional_auth_fields(client: AuthClient) -> None:
    response = _login_response()
    payload = response["data"]["xSLoginToken"]
    for key in ("refreshToken", "lang", "legals", "changePassword"):
        payload.pop(key)
    _set_query_result(client, response)

    result = await client.login("[REDACTED]", "[REDACTED]")

    assert isinstance(result, AuthDTO)
    assert result.refresh_token is None
    assert result.lang is None
    assert result.legals is None
    assert result.change_password is None


@pytest.mark.asyncio
async def test_login_translates_transport_failure_to_connection_error(
    client: AuthClient,
) -> None:
    setattr(client, "_execute_query_direct", AsyncMock(side_effect=TimeoutError))

    with pytest.raises(MyVerisureTimeoutError, match="timed out"):
        await client.login("[REDACTED]", "[REDACTED]")


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials_graphql_error(client: AuthClient) -> None:
    _set_query_result(
        client,
        {"errors": [{"message": "invalid credentials", "data": {"err": "60091"}}]},
    )

    with pytest.raises(MyVerisureAuthenticationError, match="Invalid user or password"):
        await client.login("[REDACTED]", "[REDACTED]")


@pytest.mark.asyncio
async def test_login_does_not_persist_from_client(client: AuthClient) -> None:
    _set_query_result(client, _login_response())

    result = await client.login("[REDACTED]", "[REDACTED]")

    assert isinstance(result, AuthDTO)
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_login_rejects_success_without_hash(client: AuthClient) -> None:
    _set_query_result(client, _login_response(hash=None))

    with pytest.raises(MyVerisureAuthenticationError, match="Authentication response failed"):
        await client.login("[REDACTED]", "[REDACTED]")

    update_credentials = cast(
        AsyncMock, client._resolve_session_manager().async_update_credentials
    )
    update_credentials.assert_not_awaited()


@pytest.mark.asyncio
async def test_login_returns_device_check_result_without_persisting(client: AuthClient) -> None:
    _set_query_result(client, _login_response(needDeviceAuthorization=True))
    authorized = AuthDTO(
        res="OK",
        msg="Device already authorized",
        hash="[REDACTED]",
        refresh_token="[REDACTED]",
    )
    setattr(client, "_check_device_authorization", AsyncMock(return_value=authorized))

    result = await client.login("[REDACTED]", "[REDACTED]")

    assert result is authorized
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_login_clears_pending_state_on_cancellation(client: AuthClient) -> None:
    setattr(client, "_execute_query_direct", AsyncMock(side_effect=asyncio.CancelledError()))

    with pytest.raises(asyncio.CancelledError):
        await client.login("[REDACTED]", "[REDACTED]")

    assert client._pending_session_data is None
    assert client._pending_hash is None
    assert client._otp_data is None


@pytest.mark.asyncio
async def test_malformed_otp_challenge_clears_pending_state(client: AuthClient) -> None:
    client._pending_session_data = {"user": "OLD_USER"}
    client._pending_hash = "OLD_HASH"

    with pytest.raises(MyVerisureOTPError, match="Invalid OTP data"):
        await client._handle_otp_authentication({"auth-phones": [], "auth-otp-hash": ""})

    assert client._pending_session_data is None
    assert client._pending_hash is None
    assert client._otp_data is None


@pytest.mark.asyncio
async def test_login_clears_previous_otp_and_pending_state_on_failure(
    client: AuthClient,
) -> None:
    client._otp_data = {"otp_hash": "OLD_HASH"}
    client._pending_hash = "OLD_PENDING_HASH"
    client._pending_session_data = {"user": "OLD_USER"}
    setattr(
        client,
        "_execute_query_direct",
        AsyncMock(side_effect=MyVerisureAuthenticationError("login failed")),
    )

    with pytest.raises(MyVerisureAuthenticationError):
        await client.login("[REDACTED]", "[REDACTED]")

    assert client._otp_data is None
    assert client._pending_hash is None
    assert client._pending_session_data is None


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
        await client.login("[REDACTED]", "[REDACTED]")

    check_authorization.assert_awaited_once()
    assert check_authorization.await_args is not None
    assert set(check_authorization.await_args.kwargs) == {
        "session_data",
        "hash_token",
        "refresh_token",
    }
    complete_authorization.assert_awaited_once_with()
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_login_does_not_turn_unexpected_device_check_into_otp(
    client: AuthClient,
) -> None:
    _set_query_result(client, _login_response(needDeviceAuthorization=True))
    setattr(
        client,
        "_check_device_authorization",
        AsyncMock(side_effect=RuntimeError("provider response")),
    )
    complete_authorization = AsyncMock()
    setattr(client, "_complete_device_authorization", complete_authorization)

    with pytest.raises(MyVerisureAuthenticationError, match="Login failed"):
        await client.login("[REDACTED]", "[REDACTED]")

    complete_authorization.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_device_authorization_rejects_explicit_provider_failure(
    client: AuthClient,
) -> None:
    _set_query_result(
        client,
        {"errors": [{"message": "provider failure", "data": {"auth-code": "60091"}}]},
    )

    with pytest.raises(MyVerisureAuthenticationError, match="Device authorization"):
        await client._check_device_authorization()


@pytest.mark.asyncio
async def test_post_otp_login_propagates_transport_error(client: AuthClient) -> None:
    client._resolve_session_manager().password = "[REDACTED]"
    setattr(
        client,
        "_execute_query_direct",
        AsyncMock(side_effect=MyVerisureConnectionError("offline")),
    )

    with pytest.raises(MyVerisureConnectionError, match="offline"):
        await client._perform_post_otp_login()


@pytest.mark.asyncio
async def test_post_otp_login_propagates_timeout_error(client: AuthClient) -> None:
    client._resolve_session_manager().password = "[REDACTED]"
    setattr(client, "_execute_query_direct", AsyncMock(side_effect=TimeoutError("offline")))

    with pytest.raises(MyVerisureTimeoutError, match="timed out"):
        await client._perform_post_otp_login()


@pytest.mark.asyncio
async def test_post_otp_login_propagates_aiohttp_error(client: AuthClient) -> None:
    client._resolve_session_manager().password = "[REDACTED]"
    setattr(
        client,
        "_execute_query_direct",
        AsyncMock(side_effect=aiohttp.ClientError("offline")),
    )

    with pytest.raises(MyVerisureConnectionError, match="transport failed"):
        await client._perform_post_otp_login()


@pytest.mark.asyncio
async def test_post_otp_login_does_not_persist_duplicate_session(client: AuthClient) -> None:
    client._resolve_session_manager().password = "[REDACTED]"
    _set_query_result(client, _login_response())
    result = await client._perform_post_otp_login()

    assert result.res == "OK"
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_post_otp_login_does_not_mutate_client_before_persistence(
    client: AuthClient,
) -> None:
    client._resolve_session_manager().password = "[REDACTED]"
    _set_query_result(client, _login_response())

    result = await client._perform_post_otp_login()

    assert result.hash == "[REDACTED]"
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_post_otp_login_rejects_missing_session_hash(client: AuthClient) -> None:
    client._resolve_session_manager().password = "[REDACTED]"
    _set_query_result(
        client,
        {
            "data": {
                "xSLoginToken": {
                    "res": "OK",
                    "msg": "OK",
                    "refreshToken": "[REDACTED]",
                    "needDeviceAuthorization": False,
                }
            }
        },
    )

    with pytest.raises(MyVerisureAuthenticationError, match="session hash"):
        await client._perform_post_otp_login()


@pytest.mark.asyncio
async def test_login_propagates_device_check_connection_error(
    client: AuthClient,
) -> None:
    _set_query_result(client, _login_response(needDeviceAuthorization=True))
    connection_error = MyVerisureConnectionError("offline")
    setattr(client, "_check_device_authorization", AsyncMock(side_effect=connection_error))
    complete_authorization = AsyncMock()
    setattr(client, "_complete_device_authorization", complete_authorization)

    with pytest.raises(MyVerisureConnectionError, match="offline"):
        await client.login("[REDACTED]", "[REDACTED]")

    complete_authorization.assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_device_authorization_returns_fresh_session(client: AuthClient) -> None:
    response = {
        "res": "OK",
        "msg": "OK",
        "hash": "[REDACTED]",
        "refreshToken": "[REDACTED]",
        "needDeviceAuthorization": False,
    }
    _set_query_result(client, {"data": {"xSValidateDevice": response}})

    result = await client._complete_device_authorization()

    assert result.res == "OK"
    assert result.hash == "[REDACTED]"
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_complete_device_authorization_does_not_persist_session(client: AuthClient) -> None:
    response = {
        "res": "OK",
        "msg": "OK",
        "hash": "[REDACTED]",
        "refreshToken": "[REDACTED]",
        "needDeviceAuthorization": False,
    }
    _set_query_result(client, {"data": {"xSValidateDevice": response}})

    result = await client._complete_device_authorization()

    assert result.hash == "[REDACTED]"
    cast(AsyncMock, client._resolve_session_manager().async_update_credentials).assert_not_awaited()


@pytest.mark.asyncio
async def test_check_device_authorization_accepts_validate_device_graphql_envelope(
    client: AuthClient,
) -> None:
    _set_query_result(
        client,
        {"data": {"xSValidateDevice": {"res": "OK"}}},
    )

    result = await client._check_device_authorization()

    assert result.res == "OK"
    assert result.need_device_authorization is False


@pytest.mark.asyncio
async def test_otp_challenge_is_exposed_on_otp_error_for_application_flow(
    client: AuthClient,
) -> None:
    """OTP metadata crosses the client boundary without exposing private state."""
    with pytest.raises(MyVerisureOTPError) as raised:
        await client._handle_otp_authentication(
            {
                "auth-phones": [{"id": 7, "recordId": 70, "phone": "[REDACTED]"}],
                "auth-otp-hash": "[REDACTED]",
            }
        )

    error = raised.value
    assert error.phones[0].id == 7
    assert error.otp_hash == "[REDACTED]"


@pytest.mark.asyncio
async def test_send_otp_returns_true_for_successful_response(client: AuthClient) -> None:
    _set_query_result(
        client,
        {"data": {"xSSendOtp": {"res": "OK", "msg": "sent"}}},
    )
    client._otp_data = {
        "phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}],
        "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"},
        "otp_hash": "[REDACTED]",
    }

    assert await client.send_otp(70, "[REDACTED]") is True
    assert client._otp_data["otp_hash"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_send_otp_rejects_record_outside_active_challenge(client: AuthClient) -> None:
    client._otp_data = {
        "phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}],
        "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"},
        "otp_hash": "[REDACTED]",
    }
    execute_query = AsyncMock()
    setattr(client, "_execute_query_direct", execute_query)

    with pytest.raises(MyVerisureOTPError, match="record"):
        await client.send_otp(71, "[REDACTED]")

    execute_query.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_otp_rejects_graphql_error(client: AuthClient) -> None:
    client._otp_data = {
        "phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}],
        "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"},
        "otp_hash": "[REDACTED]",
    }
    _set_query_result(client, {"errors": [{"message": "delivery failed"}]})

    with pytest.raises(MyVerisureOTPError, match="delivery failed"):
        await client.send_otp(70, "[REDACTED]")


@pytest.mark.asyncio
async def test_post_otp_login_rejects_present_but_empty_errors_envelope(client: AuthClient) -> None:
    _set_query_result(client, {"errors": [], "data": {"xSLoginToken": {"res": "OK"}}})

    with pytest.raises(MyVerisureAuthenticationError, match="Post-OTP login failed"):
        await client._perform_post_otp_login()


@pytest.mark.asyncio
async def test_send_otp_rejects_present_but_empty_errors_envelope(client: AuthClient) -> None:
    client._otp_data = {
        "phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}],
        "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"},
        "otp_hash": "[REDACTED]",
    }
    _set_query_result(
        client,
        {"errors": [], "data": {"xSSendOtp": {"res": "OK"}}},
    )

    with pytest.raises(MyVerisureOTPError, match="delivery failed"):
        await client.send_otp(70, "[REDACTED]")


@pytest.mark.asyncio
async def test_send_otp_rejects_empty_provider_payload(client: AuthClient) -> None:
    client._otp_data = {
        "phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}],
        "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"},
        "otp_hash": "[REDACTED]",
    }
    _set_query_result(client, {"data": {"xSSendOtp": {}}})

    with pytest.raises(MyVerisureOTPError, match="No response data"):
        await client.send_otp(70, "[REDACTED]")


@pytest.mark.asyncio
async def test_verify_otp_rejects_missing_or_expired_client_challenge(client: AuthClient) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    client._otp_expires_at = None
    provider = AsyncMock()
    setattr(client, "_execute_query_direct", provider)

    with pytest.raises(MyVerisureOTPError, match="expired"):
        await client.verify_otp("OTP_SENTINEL")

    client._otp_data = {"phones": [], "otp_hash": "[REDACTED]"}
    client._otp_expires_at = time.monotonic() - 1
    with pytest.raises(MyVerisureOTPError, match="expired"):
        await client.verify_otp("OTP_SENTINEL")
    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_otp_rejects_replayed_client_challenge(client: AuthClient) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    client._otp_expires_at = time.monotonic() + 300
    client._otp_consumed = True
    provider = AsyncMock()
    setattr(client, "_execute_query_direct", provider)

    with pytest.raises(MyVerisureOTPError, match="consumed"):
        await client.verify_otp("OTP_SENTINEL")

    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_otp_requires_stored_otp_data(client: AuthClient) -> None:
    with pytest.raises(MyVerisureOTPError, match="challenge unavailable"):
        await client.verify_otp("123456")


@pytest.mark.asyncio
async def test_verify_otp_rejects_empty_code_before_provider(client: AuthClient) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    execute_query = AsyncMock()
    setattr(client, "_execute_query_direct", execute_query)

    with pytest.raises(MyVerisureOTPError, match="code"):
        await client.verify_otp("   ")

    execute_query.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_otp_rejects_unsuccessful_validation(client: AuthClient) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    _set_query_result(
        client,
        {"data": {"xSValidateDevice": {"res": "ERROR", "msg": "invalid code"}}},
    )

    with pytest.raises(MyVerisureOTPError, match="invalid code"):
        await client.verify_otp("123456")

    assert client._otp_data is not None
    assert client._otp_consumed is False


@pytest.mark.asyncio
async def test_verify_otp_consumes_challenge_before_post_login_failure(
    client: AuthClient,
) -> None:
    client._otp_data = {
        "phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}],
        "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"},
        "otp_hash": "[REDACTED]",
    }
    client._otp_expires_at = time.monotonic() + 300
    client._pending_session_data = {"user": "PENDING"}
    client._pending_hash = "PENDING_HASH"
    client._pending_refresh_token = "PENDING_REFRESH"
    client._pending_user = "PENDING_USER"
    client._pending_password = "PENDING_PASSWORD"
    _set_query_result(
        client,
        {"data": {"xSValidateDevice": {"res": "OK", "hash": "fresh", "needDeviceAuthorization": False}}},
    )
    post_otp_login = AsyncMock(side_effect=MyVerisureConnectionError("post login"))
    setattr(client, "_perform_post_otp_login", post_otp_login)

    with pytest.raises(MyVerisureConnectionError):
        await client.verify_otp("123456")

    assert client._otp_consumed is True
    assert client._pending_session_data is None
    assert client._pending_hash is None
    assert client._pending_refresh_token is None
    assert client._pending_user is None
    assert client._pending_password is None
    provider = AsyncMock()
    setattr(client, "_execute_query_direct", provider)
    with pytest.raises(MyVerisureOTPError, match="unavailable"):
        await client.verify_otp("123456")
    provider.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_otp_sends_security_contract_and_refreshes_session(
    client: AuthClient,
) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    _set_query_result(
        client,
        {
            "data": {
                "xSValidateDevice": {
                    "res": "OK",
                    "hash": "otp-[REDACTED]",
                    "refreshToken": "otp-[REDACTED]",
                    "needDeviceAuthorization": False,
                }
            }
        },
    )
    post_otp_login = AsyncMock(
        return_value=AuthDTO(
            res="OK",
            msg="fresh session",
            hash="[REDACTED]",
            refresh_token="[REDACTED]",
        )
    )
    setattr(client, "_perform_post_otp_login", post_otp_login)

    result = await client.verify_otp("123456")

    assert result.hash == "[REDACTED]"
    post_otp_login.assert_awaited_once_with()
    execute_query = cast(AsyncMock, client._execute_query_direct)
    assert execute_query.await_args is not None
    request_headers = execute_query.await_args.args[2]
    security = json.loads(request_headers["Security"])
    assert security == {"token": "123456", "type": "OTP", "otpHash": "[REDACTED]"}


@pytest.mark.asyncio
async def test_verify_otp_propagates_post_otp_os_error(
    client: AuthClient,
) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    _set_query_result(
        client,
        {
            "data": {
                "xSValidateDevice": {
                    "res": "OK",
                    "hash": "[REDACTED]",
                    "refreshToken": "[REDACTED]",
                    "needDeviceAuthorization": False,
                }
            }
        },
    )
    setattr(client, "_perform_post_otp_login", AsyncMock(side_effect=OSError("offline")))

    with pytest.raises(MyVerisureConnectionError, match="transport failed"):
        await client.verify_otp("123456")


@pytest.mark.asyncio
async def test_verify_otp_propagates_post_otp_connection_error(
    client: AuthClient,
) -> None:
    client._otp_data = {"phones": [{"id": 7, "record_id": 70, "phone": "[REDACTED]"}], "selected_phone": {"id": 7, "record_id": 70, "phone": "[REDACTED]"}, "otp_hash": "[REDACTED]"}
    _set_query_result(
        client,
        {
            "data": {
                "xSValidateDevice": {
                    "res": "OK",
                    "hash": "[REDACTED]",
                    "refreshToken": "[REDACTED]",
                    "needDeviceAuthorization": False,
                }
            }
        },
    )
    setattr(
        client,
        "_perform_post_otp_login",
        AsyncMock(side_effect=MyVerisureConnectionError("offline")),
    )

    with pytest.raises(MyVerisureConnectionError, match="offline"):
        await client.verify_otp("123456")

"""Current provider native authentication contract.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json
import base64
import time
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.auth_client import AuthClient
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.application.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureOTPError,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager
from custom_components.my_verisure.core.application.auth_session_persistence import AuthSessionPersistence
from custom_components.my_verisure.core.repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from custom_components.my_verisure.core.use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl


def native_success():
    return {"data": {"xSLoginToken": {
        "res": "OK", "msg": "auth-api.login.success", "hash": "native-token",
        "refreshToken": "native-refresh", "needDeviceAuthorization": None,
        "lang": "es", "legals": True, "changePassword": False,
    }}}


@pytest.mark.asyncio
async def test_current_native_login_preserves_device_and_accepts_verified_response(tmp_path):
    session = SessionManager(file_manager=FileManager(tmp_path))
    device = DeviceManager(FileManager(tmp_path))
    await device.async_ensure_device_identifiers()
    before = device.get_device_identifiers()
    client = AuthClient(session, device)
    client._execute_query_direct = AsyncMock(return_value=native_success())

    result = await client.login("synthetic-user", "synthetic-password")

    assert result.need_device_authorization is False
    assert result.hash == "native-token"
    assert result.refresh_token == "native-refresh"
    variables = client._execute_query_direct.await_args.args[1]
    assert variables["callby"] == "OWI_10"
    assert variables["deviceVersion"] == "10.192.1"
    assert variables["deviceOsVersion"] == "27.2"
    assert variables["idDevice"] == before["idDevice"]
    assert variables["uuid"] == before["uuid"]
    assert variables["deviceUseBiometric"] == "DISABLED"
    assert variables["phoneAsLogin"] is False
    headers = client._execute_query_direct.await_args.args[2]
    assert json.loads(headers["App"])["origin"] == "native"
    assert session.hash_token is None


@pytest.mark.asyncio
@pytest.mark.parametrize("android", [False, True])
async def test_native_refresh_rotates_token_without_password_login(tmp_path, android):
    session = SessionManager(file_manager=FileManager(tmp_path))
    session.username = "synthetic-user"
    session.password = "synthetic-password"
    session.refresh_token = "stored-refresh"
    device = DeviceManager(FileManager(tmp_path))
    if android:
        await device.async_set_push_token("synthetic-fcm-token")
    client = AuthClient(session, device)
    response = {"data": {"xSRefreshLogin": native_success()["data"]["xSLoginToken"]}}
    client._execute_query_direct = AsyncMock(return_value=response)

    result = await client.login("synthetic-user", "synthetic-password")

    assert result.refresh_token == "native-refresh"
    query, variables, _headers = client._execute_query_direct.await_args.args
    assert "xSRefreshLogin" in query
    assert variables["refreshToken"] == "stored-refresh"
    assert variables["callby"] == ("OWA_10" if android else "OWI_10")
    assert variables["deviceOsVersion"] == ("16" if android else "27.2")
    if android:
        assert variables["idDevice"] == "synthetic-fcm-token"
    assert "password" not in variables
    client._execute_query_direct.assert_awaited_once()
    assert session.refresh_token == "stored-refresh"


@pytest.mark.asyncio
async def test_native_refresh_rejection_falls_back_once_to_device_login(tmp_path):
    session = SessionManager(file_manager=FileManager(tmp_path))
    session.username = "synthetic-user"
    session.password = "synthetic-password"
    session.refresh_token = "expired-refresh"
    client = AuthClient(session, DeviceManager(FileManager(tmp_path)))
    client._execute_query_direct = AsyncMock(side_effect=[
        {"errors": [{"message": "Unauthorized"}]}, native_success(),
    ])

    result = await client.login("synthetic-user", "synthetic-password")

    assert result.hash == "native-token"
    assert client._execute_query_direct.await_count == 2
    assert "password" in client._execute_query_direct.await_args_list[1].args[1]


@pytest.mark.asyncio
async def test_native_profile_upgrade_keeps_registered_identifiers(tmp_path):
    device = DeviceManager(FileManager(tmp_path))
    await device.async_ensure_device_identifiers()
    original = device.get_device_identifiers()
    device._device_identifiers.update(deviceVersion="10.154.0", deviceOsVersion="Linux 6.12")

    for variables in (device.get_login_variables("session-id"), device.get_validation_variables()):
        assert variables["deviceVersion"] == "10.192.1"
        assert variables["deviceOsVersion"] == "27.2"
        assert variables["idDevice"] == original["idDevice"]
        assert variables["uuid"] == original["uuid"]


@pytest.mark.asyncio
async def test_native_challenge_without_token_completes_sms_and_device_login_without_early_commit(tmp_path):
    session = SessionManager(file_manager=FileManager(tmp_path))
    device = DeviceManager(FileManager(tmp_path))
    client = AuthClient(session, device)
    transport = AsyncMock(side_effect=[
        {"data": {"xSLoginToken": {
            "res": "OK", "msg": "OK", "hash": None, "lang": "es", "legals": None,
            "changePassword": False, "needDeviceAuthorization": True,
        }}},
        {"errors": [{"message": "Unauthorized", "data": {
            "auth-type": "OTP", "auth-code": "10001",
            "auth-phones": [{"id": 0, "phone": "******08"}],
            "auth-otp-hash": "synthetic-challenge",
        }}]},
        {"data": {"xSSendOtp": {"res": "OK"}}},
        {"data": {"xSValidateDevice": {
            "res": "OK", "hash": "synthetic-token", "refreshToken": "synthetic-refresh",
            "legals": None,
        }}},
        native_success(),
    ])
    client._execute_query_direct = transport

    with pytest.raises(MyVerisureOTPError) as challenge:
        await client.login("synthetic-user", "synthetic-password")

    assert len(challenge.value.phones) == 1
    assert session.hash_token is None
    assert not session.is_authenticated
    assert transport.await_count == 2
    login_variables = transport.await_args_list[0].args[1]
    assert login_variables["callby"] == "OWI_10"
    assert login_variables["deviceOsVersion"] == "27.2"
    headers = transport.await_args_list[0].args[2]
    assert json.loads(headers["App"])["origin"] == "native"

    assert client.select_phone(0)
    assert await client.send_otp(0, "synthetic-challenge")
    pending_auth = json.loads(transport.await_args_list[2].args[2]["auth"])
    assert pending_auth["hash"] is None
    assert transport.await_args_list[2].args[2]["app-origin"] == "web"
    assert transport.await_args_list[2].args[2]["app-version"] == "10.192.1"
    assert transport.await_args_list[1].args[1]["uuid"] == login_variables["uuid"]
    assert session.hash_token is None

    result = await client.verify_otp("123456")

    assert result.hash == "native-token"
    assert result.need_device_authorization is False
    assert session.hash_token is None
    assert transport.await_count == 5
    assert client._pending_user is None


@pytest.mark.parametrize("context", [{}, {"user": "synthetic-user"}])
def test_tokenless_context_cannot_authenticate_alarm_requests(tmp_path, context):
    session = SessionManager(file_manager=FileManager(tmp_path))
    client = AuthClient(session, Mock())

    with pytest.raises(MyVerisureAuthenticationError):
        client._get_session_headers(context, None)
    with pytest.raises(MyVerisureAuthenticationError):
        client._get_authentication_headers(context, None)


@pytest.mark.asyncio
async def test_refresh_transport_failure_does_not_retry_password_login(tmp_path):
    session = SessionManager(file_manager=FileManager(tmp_path))
    session.username = "synthetic-user"
    session.password = "synthetic-password"
    session.refresh_token = "stored-refresh"
    client = AuthClient(session, DeviceManager(FileManager(tmp_path)))
    client._execute_query_direct = AsyncMock(side_effect=MyVerisureConnectionError("offline"))

    with pytest.raises(MyVerisureConnectionError):
        await client.login("synthetic-user", "synthetic-password")

    client._execute_query_direct.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_token_is_never_used_for_another_account(tmp_path):
    session = SessionManager(file_manager=FileManager(tmp_path))
    session.username = "other-user"
    session.refresh_token = "other-refresh"
    client = AuthClient(session, DeviceManager(FileManager(tmp_path)))
    client._execute_query_direct = AsyncMock(return_value=native_success())

    await client.login("synthetic-user", "synthetic-password")

    variables = client._execute_query_direct.await_args.args[1]
    assert "refreshToken" not in variables
    assert variables["user"] == "synthetic-user"


@pytest.mark.asyncio
async def test_native_session_survives_restart_and_persists_rotated_refresh(tmp_path):
    def access_token(marker):
        return ".".join(
            base64.urlsafe_b64encode(part).decode().rstrip("=")
            for part in (
                b"{}", json.dumps({"exp": time.time() + 3600, "jti": marker}).encode(),
                b"synthetic-signature",
            )
        )

    storage = FileManager(tmp_path)
    first = SessionManager(file_manager=storage)
    device = DeviceManager(storage)
    client = AuthClient(first, device)
    initial_response = native_success()
    initial_response["data"]["xSLoginToken"]["hash"] = access_token("initial")
    client._execute_query_direct = AsyncMock(return_value=initial_response)
    use_case = AuthUseCaseImpl(AuthRepositoryImpl(client), AuthSessionPersistence(first))
    await use_case.login("synthetic-user", "synthetic-password")
    registered_id = device.get_device_identifiers()["uuid"]

    reloaded = SessionManager(file_manager=storage)
    await reloaded.async_load_session_from_disk()
    assert reloaded.refresh_token == "native-refresh"
    reloaded.session_timestamp = 0
    second_device = DeviceManager(storage)
    second_client = AuthClient(reloaded, second_device)
    refreshed = dict(native_success()["data"]["xSLoginToken"])
    rotated_access = access_token("rotated")
    refreshed.update(hash=rotated_access, refreshToken="rotated-refresh")
    second_client._execute_query_direct = AsyncMock(return_value={
        "data": {"xSRefreshLogin": refreshed},
    })
    second_use_case = AuthUseCaseImpl(
        AuthRepositoryImpl(second_client), AuthSessionPersistence(reloaded)
    )
    reloaded.set_authenticator(second_use_case.login)

    assert await reloaded.ensure_authenticated(interactive=False)

    assert second_device.get_device_identifiers()["uuid"] == registered_id
    second_client._execute_query_direct.assert_awaited_once()
    final = SessionManager(file_manager=storage)
    await final.async_load_session_from_disk()
    assert final.hash_token == rotated_access
    assert final.refresh_token == "rotated-refresh"
    assert final.is_session_valid()


@pytest.mark.asyncio
async def test_selected_zero_phone_reaches_provider_client_through_application(tmp_path):
    storage = FileManager(tmp_path)
    session = SessionManager(file_manager=storage)
    client = AuthClient(session, DeviceManager(storage))
    client._execute_query_direct = AsyncMock(side_effect=[
        {"data": {"xSLoginToken": {
            "res": "OK", "msg": "auth-api.mfa_needed", "hash": None,
            "needDeviceAuthorization": True,
        }}},
        {"data": {"xSValidateDevice": None}, "errors": [{"data": {
            "auth-type": "OTP", "auth-code": "10001",
            "auth-phones": [{"id": 0, "phone": "******08"}],
            "auth-otp-hash": "synthetic-challenge",
        }}]},
        {"data": {"xSSendOtp": {"res": "OK"}}},
    ])
    use_case = AuthUseCaseImpl(AuthRepositoryImpl(client), AuthSessionPersistence(session))
    with pytest.raises(MyVerisureOTPError):
        await use_case.login("synthetic-user", "synthetic-password")

    assert use_case.select_phone(0)
    assert await use_case.send_otp(0)

    assert client._execute_query_direct.await_count == 3
    assert client._execute_query_direct.await_args.args[1]["recordId"] == 0
    assert session.hash_token is None

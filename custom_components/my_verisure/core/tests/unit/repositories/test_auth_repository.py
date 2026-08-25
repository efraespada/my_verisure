"""Unit tests for current authentication repository contracts."""

from unittest.mock import AsyncMock, Mock

import aiohttp
import pytest

from ....api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureOTPError,
    MyVerisureTimeoutError,
)
from ....application.models.auth import Auth
from ....api.models.dto.auth_dto import AuthDTO
from ....repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from ....repositories.interfaces.auth_repository import AuthRepository


@pytest.fixture
def client():
    value = Mock()
    value.login = AsyncMock()
    value.send_otp = AsyncMock()
    value.verify_otp = AsyncMock()
    value.get_available_phones = Mock()
    value.invalidate_otp_challenge = Mock()
    return value


@pytest.fixture
def repository(client):
    return AuthRepositoryImpl(client)


def test_implements_interface(repository):
    assert isinstance(repository, AuthRepository)


@pytest.mark.asyncio
async def test_login_success(repository, client):
    client.login.return_value = AuthDTO(
        res="OK",
        msg="Login successful",
        hash="HASH_SENTINEL",
        refresh_token="REFRESH_SENTINEL",
        lang="es",
        legals=True,
        need_device_authorization=False,
    )
    result = await repository.login(Auth("USER_SENTINEL", "PASSWORD_SENTINEL"))
    assert result.success is True
    assert result.hash == "HASH_SENTINEL"
    client.login.assert_awaited_once_with("USER_SENTINEL", "PASSWORD_SENTINEL")


@pytest.mark.asyncio
async def test_login_authentication_error_returns_failure(repository, client):
    client.login.side_effect = MyVerisureAuthenticationError("invalid")
    result = await repository.login(Auth("[REDACTED]", "[REDACTED]"))
    assert result.success is False
    assert "invalid" in result.message


@pytest.mark.asyncio
async def test_login_propagates_connection_error(repository, client):
    client.login.side_effect = MyVerisureConnectionError("offline")

    with pytest.raises(MyVerisureConnectionError, match="offline"):
        await repository.login(Auth("[REDACTED]", "[REDACTED]"))


@pytest.mark.asyncio
async def test_login_translates_os_error_to_connection_error(repository, client):
    client.login.side_effect = OSError("raw transport detail")

    with pytest.raises(MyVerisureConnectionError, match="transport"):
        await repository.login(Auth("[REDACTED]", "[REDACTED]"))


@pytest.mark.asyncio
async def test_login_otp_error_is_propagated(repository, client):
    client.login.side_effect = MyVerisureOTPError("otp")
    with pytest.raises(MyVerisureOTPError, match="otp"):
        await repository.login(Auth("[REDACTED]", "[REDACTED]"))


@pytest.mark.asyncio
async def test_verify_otp_preserves_device_authorization_failure(repository, client):
    client.verify_otp.side_effect = MyVerisureDeviceAuthorizationError("device")

    with pytest.raises(MyVerisureDeviceAuthorizationError, match="device"):
        await repository.verify_otp("OTP_SENTINEL")


def test_get_available_phones_propagates_lookup_error(repository, client):
    client.get_available_phones.side_effect = RuntimeError("network")

    with pytest.raises(MyVerisureConnectionError, match="phone lookup"):
        repository.get_available_phones()


def test_get_available_phones(repository, client):
    client.get_available_phones.return_value = [{"id": 1, "phone": "masked"}]
    assert repository.get_available_phones() == [{"id": 1, "phone": "masked"}]


@pytest.mark.asyncio
async def test_send_otp(repository, client):
    client.send_otp.return_value = True
    assert await repository.send_otp(1, "hash") is True
    client.send_otp.assert_awaited_once_with(1, "hash")


@pytest.mark.asyncio
async def test_send_otp_propagates_connection_error(repository, client):
    client.send_otp.side_effect = MyVerisureConnectionError("offline")

    with pytest.raises(MyVerisureConnectionError, match="offline"):
        await repository.send_otp(1, "[REDACTED]")


@pytest.mark.asyncio
async def test_send_otp_unexpected_error_is_connection_failure(repository, client):
    client.send_otp.side_effect = RuntimeError("network")
    with pytest.raises(MyVerisureConnectionError, match="transport"):
        await repository.send_otp(1, "hash")


@pytest.mark.asyncio
async def test_verify_otp_uses_fresh_auth_dto_tokens(repository, client):
    client._hash = "OLD_HASH_SENTINEL"
    client._refresh_token = "OLD_REFRESH_SENTINEL"
    client.verify_otp.return_value = AuthDTO(
        res="OK",
        msg="OTP verified",
        hash="FRESH_HASH_SENTINEL",
        refresh_token="FRESH_REFRESH_SENTINEL",
        need_device_authorization=False,
    )

    result = await repository.verify_otp("[REDACTED]")

    assert result.success is True
    assert result.hash == "FRESH_HASH_SENTINEL"
    assert result.refresh_token == "FRESH_REFRESH_SENTINEL"


@pytest.mark.asyncio
async def test_verify_otp_success(repository, client):
    client.verify_otp.return_value = AuthDTO(
        res="OK",
        msg="OTP verified",
        hash="HASH_SENTINEL",
        refresh_token="REFRESH_SENTINEL",
        need_device_authorization=False,
    )
    result = await repository.verify_otp("[REDACTED]")
    assert result.success is True
    client.verify_otp.assert_awaited_once_with("[REDACTED]")


@pytest.mark.asyncio
async def test_verify_otp_propagates_connection_error(repository, client):
    client.verify_otp.side_effect = MyVerisureConnectionError("offline")

    with pytest.raises(MyVerisureConnectionError, match="offline"):
        await repository.verify_otp("[REDACTED]")


@pytest.mark.asyncio
async def test_verify_otp_propagates_timeout_error(repository, client):
    client.verify_otp.side_effect = TimeoutError("offline")

    with pytest.raises(MyVerisureTimeoutError, match="timed out"):
        await repository.verify_otp("123456")


@pytest.mark.asyncio
async def test_verify_otp_propagates_aiohttp_error(repository, client):
    client.verify_otp.side_effect = aiohttp.ClientError("offline")

    with pytest.raises(MyVerisureConnectionError, match="transport"):
        await repository.verify_otp("[REDACTED]")


@pytest.mark.asyncio
async def test_verify_otp_unexpected_error_is_connection_failure(repository, client):
    client.verify_otp.side_effect = RuntimeError("invalid")
    with pytest.raises(MyVerisureConnectionError, match="transport"):
        await repository.verify_otp("[REDACTED]")

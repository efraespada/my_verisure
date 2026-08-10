"""Unit tests for current authentication repository contracts."""

from unittest.mock import AsyncMock, Mock

import pytest

from ....api.exceptions import MyVerisureAuthenticationError, MyVerisureOTPError
from ....api.models.domain.auth import Auth
from ....repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from ....repositories.interfaces.auth_repository import AuthRepository


@pytest.fixture
def client():
    value = Mock()
    value.login = AsyncMock()
    value.send_otp = AsyncMock()
    value.verify_otp = AsyncMock()
    value.get_available_phones = Mock()
    value._hash = "hash"
    value._refresh_token = "refresh"
    value._session_data = {"lang": "es", "legals": True}
    return value


@pytest.fixture
def repository(client):
    return AuthRepositoryImpl(client)


def test_implements_interface(repository):
    assert isinstance(repository, AuthRepository)


@pytest.mark.asyncio
async def test_login_success(repository, client):
    client.login.return_value = True
    result = await repository.login(Auth("user", "password"))
    assert result.success is True
    assert result.hash == "hash"
    client.login.assert_awaited_once_with("user", "password")


@pytest.mark.asyncio
async def test_login_authentication_error_returns_failure(repository, client):
    client.login.side_effect = MyVerisureAuthenticationError("invalid")
    result = await repository.login(Auth("user", "password"))
    assert result.success is False
    assert "invalid" in result.message


@pytest.mark.asyncio
async def test_login_otp_error_is_propagated(repository, client):
    client.login.side_effect = MyVerisureOTPError("otp")
    with pytest.raises(MyVerisureOTPError, match="otp"):
        await repository.login(Auth("user", "password"))


def test_get_available_phones(repository, client):
    client.get_available_phones.return_value = [{"id": 1, "phone": "masked"}]
    assert repository.get_available_phones() == [{"id": 1, "phone": "masked"}]


@pytest.mark.asyncio
async def test_send_otp(repository, client):
    client.send_otp.return_value = True
    assert await repository.send_otp(1, "hash") is True
    client.send_otp.assert_awaited_once_with(1, "hash")


@pytest.mark.asyncio
async def test_send_otp_error_is_wrapped(repository, client):
    client.send_otp.side_effect = RuntimeError("network")
    with pytest.raises(MyVerisureOTPError, match="network"):
        await repository.send_otp(1, "hash")


@pytest.mark.asyncio
async def test_verify_otp_success(repository, client):
    client.verify_otp.return_value = True
    result = await repository.verify_otp("123456")
    assert result.success is True
    client.verify_otp.assert_awaited_once_with("123456")


@pytest.mark.asyncio
async def test_verify_otp_error_is_wrapped(repository, client):
    client.verify_otp.side_effect = RuntimeError("invalid")
    with pytest.raises(MyVerisureOTPError, match="invalid"):
        await repository.verify_otp("123456")

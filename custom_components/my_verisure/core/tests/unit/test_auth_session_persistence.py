"""Tests for entry-scoped authentication session persistence."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.auth_session_persistence import (
    AuthSessionPersistence,
)
from custom_components.my_verisure.core.application.exceptions import (
    MyVerisurePersistenceError,
)
from custom_components.my_verisure.core.application.models.auth import AuthResult
from custom_components.my_verisure.core.api.auth_session_projection import build_session_data


@pytest.mark.asyncio
async def test_persists_tokens_and_clears_service_backoff() -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock()
    policy = AuthSessionPersistence(session_manager)

    result = await policy.persist(
        user="user",
        password="password",
        hash_token="hash",
        refresh_token="refresh",
    )

    assert result == ("hash", "refresh")
    session_manager.async_update_credentials.assert_awaited_once_with(
        "user", "password", "hash", "refresh"
    )
    session_manager.clear_service_blocked.assert_called_once_with()


@pytest.mark.asyncio
async def test_persist_result_uses_explicit_pending_credentials() -> None:
    session_manager = Mock(username="OLD_USER_SENTINEL", password="OLD_PASSWORD_SENTINEL")
    session_manager.async_update_credentials = AsyncMock()
    result = AuthResult(
        success=True,
        message="ok",
        hash="HASH_SENTINEL",
        refresh_token="REFRESH_SENTINEL",
        need_device_authorization=False,
    )

    await AuthSessionPersistence(session_manager).persist_result(
        result,
        username="NEW_USER_SENTINEL",
        password="NEW_PASSWORD_SENTINEL",
    )

    session_manager.async_update_credentials.assert_awaited_once_with(
        "NEW_USER_SENTINEL",
        "NEW_PASSWORD_SENTINEL",
        "HASH_SENTINEL",
        "REFRESH_SENTINEL",
    )


@pytest.mark.asyncio
async def test_rejects_success_without_hash() -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock()

    with pytest.raises(MyVerisurePersistenceError, match="without a session hash"):
        await AuthSessionPersistence(session_manager).persist(
            user="user", password="password", hash_token="", refresh_token=None
        )

    session_manager.async_update_credentials.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_hash", [None, "   ", 123])
async def test_rejects_non_string_or_blank_hash(invalid_hash) -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock()

    with pytest.raises(MyVerisurePersistenceError, match="without a session hash"):
        await AuthSessionPersistence(session_manager).persist(
            user="user", password="password", hash_token=invalid_hash, refresh_token=None
        )

    session_manager.async_update_credentials.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_hash", [None, "   ", 123])
async def test_persist_result_rejects_invalid_hash(invalid_hash) -> None:
    session_manager = Mock(username="user", password="password")
    session_manager.async_update_credentials = AsyncMock()

    with pytest.raises(MyVerisurePersistenceError, match="without a session hash"):
        await AuthSessionPersistence(session_manager).persist_result(
            AuthResult(
                success=True,
                hash=invalid_hash,
                message="ok",
                need_device_authorization=False,
            )
        )

    session_manager.async_update_credentials.assert_not_awaited()



@pytest.mark.asyncio
@pytest.mark.parametrize("refresh_token", ["", "   ", 123, True, {}])
async def test_rejects_malformed_refresh_token(refresh_token) -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock()

    with pytest.raises(MyVerisurePersistenceError, match="refresh token"):
        await AuthSessionPersistence(session_manager).persist(
            user="USER_SENTINEL",
            password="PASSWORD_SENTINEL",
            hash_token="HASH_SENTINEL",
            refresh_token=refresh_token,
        )

    session_manager.async_update_credentials.assert_not_awaited()


@pytest.mark.asyncio
async def test_wraps_storage_failure_as_persistence_error() -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock(
        side_effect=OSError("storage failure")
    )

    with pytest.raises(MyVerisurePersistenceError, match="Session persistence failed"):
        await AuthSessionPersistence(session_manager).persist(
            user="USER_SENTINEL",
            password="PASSWORD_SENTINEL",
            hash_token="HASH_SENTINEL",
            refresh_token=None,
        )




def test_build_session_projection_omits_absent_optional_fields() -> None:
    result = build_session_data(
        "USER_SENTINEL", {"needDeviceAuthorization": False}, 42
    )

    assert result == {
        "user": "USER_SENTINEL",
        "needDeviceAuthorization": False,
        "login_time": 42,
    }


def test_builds_session_projection() -> None:
    result = build_session_data(
        "USER_SENTINEL",
        {
            "lang": "ES",
            "legals": True,
            "changePassword": False,
            "needDeviceAuthorization": False,
        },
        42,
    )

    assert result == {
        "user": "USER_SENTINEL",
        "lang": "ES",
        "legals": True,
        "changePassword": False,
        "needDeviceAuthorization": False,
        "login_time": 42,
    }

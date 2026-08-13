"""Tests for entry-scoped authentication session persistence."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.auth_session_persistence import (
    AuthSessionPersistence,
)


@pytest.mark.asyncio
async def test_persists_tokens_and_clears_service_backoff() -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock()
    policy = AuthSessionPersistence(session_manager)

    result = await policy.persist(
        user="user",
        password="password",
        login_data={"hash": "hash", "refreshToken": "refresh"},
    )

    assert result == ("hash", "refresh")
    session_manager.async_update_credentials.assert_awaited_once_with(
        "user", "password", "hash", "refresh"
    )
    session_manager.clear_service_blocked.assert_called_once_with()


@pytest.mark.asyncio
async def test_rejects_success_without_hash() -> None:
    session_manager = Mock()
    session_manager.async_update_credentials = AsyncMock()

    with pytest.raises(ValueError, match="without a session hash"):
        await AuthSessionPersistence(session_manager).persist(
            user="user", password="password", login_data={}
        )

    session_manager.async_update_credentials.assert_not_awaited()


def test_builds_session_projection() -> None:
    result = AuthSessionPersistence.build_session_data(
        "user", {"lang": "ES", "legals": True}, 42
    )

    assert result == {
        "user": "user",
        "lang": "ES",
        "legals": True,
        "changePassword": False,
        "needDeviceAuthorization": False,
        "login_time": 42,
    }

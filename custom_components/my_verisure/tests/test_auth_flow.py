"""Tests for authentication and session refresh behaviour."""

from __future__ import annotations

import time
from unittest.mock import patch

import pytest

from custom_components.my_verisure.core.application.coordinator_authentication import (
    CoordinatorAuthenticationPolicy,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@patch(
    "custom_components.my_verisure.core.session_manager.is_jwt_expired",
    return_value=False,
)
def test_token_expiration_with_60min_lifetime(
    _mock_is_jwt_expired: object, tmp_path
) -> None:
    """Session stays valid until local max age exceeds TOKEN_MAX_AGE_SECONDS."""
    session_manager = SessionManager(file_manager=FileManager(tmp_path))
    session_manager.username = "test_user"
    session_manager.password = "test_pass"
    session_manager.hash_token = "test_token"
    session_manager.session_timestamp = time.time()

    assert session_manager.is_session_valid() is True

    session_manager.session_timestamp = time.time() - (30 * 60)
    assert session_manager.is_session_valid() is True

    session_manager.session_timestamp = time.time() - (59 * 60)
    assert session_manager.is_session_valid() is True

    session_manager.session_timestamp = time.time() - (61 * 60)
    assert session_manager.is_session_valid() is False


@pytest.mark.asyncio
async def test_service_blocked_uses_cache() -> None:
    """Authentication policy returns the persisted cache when login is blocked."""
    policy = CoordinatorAuthenticationPolicy(
        login=lambda: _false(),
        load_cache=lambda: {"alarm": "armed"},
    )

    decision = await policy.authenticate()

    assert decision.authenticated is False
    assert decision.cached_data == {"alarm": "armed"}


@pytest.mark.asyncio
async def test_setup_with_expired_session_and_cache() -> None:
    """Authentication policy reports no cache when login and cache both fail."""
    policy = CoordinatorAuthenticationPolicy(
        login=lambda: _false(),
        load_cache=lambda: {},
    )

    decision = await policy.authenticate()

    assert decision.authenticated is False
    assert decision.cached_data is None


async def _false() -> bool:
    return False

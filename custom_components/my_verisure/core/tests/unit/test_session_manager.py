"""Unit tests for the current SessionManager contract."""

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from ...file_manager import FileManager
from ... import session_manager as session_module
from ...session_manager import SessionManager, get_session_manager


@pytest.fixture
def manager(tmp_path):
    with patch.object(SessionManager, "_get_session_file_path", return_value=str(tmp_path / "session.json")):
        value = SessionManager(file_manager=FileManager(tmp_path))
    return value


def test_update_credentials_persists_and_reports_authenticated(manager):
    manager.update_credentials("user", "password", "hash", "refresh")
    assert manager.is_authenticated is True
    assert manager.get_current_hash_token() == "hash"
    payload = json.loads(Path(manager.session_file).read_text())
    assert payload["username"] == "user"
    assert payload["password"] == "password"
    assert payload["hash_token"] == "hash"


def test_load_session_sync_hydrates_valid_recent_session(manager):
    payload = {"username": "user", "password": "password", "hash_token": "hash", "refresh_token": "refresh", "session_timestamp": time.time(), "current_installation": "1"}
    Path(manager.session_file).write_text(json.dumps(payload))
    with patch.object(session_module, "is_jwt_expired", return_value=False):
        manager.load_session_sync()
        assert manager.username == "user"
        assert manager.current_installation == "1"
        assert manager.is_session_valid() is True


def test_clear_credentials_removes_file(manager):
    manager.update_credentials("user", "password", "hash")
    manager.clear_credentials()
    assert manager.is_authenticated is False
    assert not Path(manager.session_file).exists()


def test_current_session_data_requires_credentials(manager):
    assert manager.get_current_session_data() is None
    manager.update_credentials("user", "password", "hash", persist=False)
    assert manager.get_current_session_data()["user"] == "user"


def test_expired_session_is_invalid(manager):
    manager.update_credentials("user", "password", "hash", persist=False)
    manager.session_timestamp = time.time() - session_module.TOKEN_MAX_AGE_SECONDS - 1
    assert manager.is_session_valid() is False


def test_missing_token_is_invalid(manager):
    manager.username = "user"
    manager.password = "password"
    assert manager.is_session_valid() is False


def test_service_blocked_cooldown(manager):
    manager.record_service_blocked(60)
    assert manager.is_service_blocked() is True
    manager.clear_service_blocked()
    assert manager.is_service_blocked() is False


def test_get_session_manager_is_singleton():
    session_module._session_manager_instance = None
    first = get_session_manager()
    second = get_session_manager()
    assert first is second
    session_module._session_manager_instance = None


@pytest.mark.asyncio
async def test_async_update_and_clear(manager):
    await manager.async_update_credentials("user", "password", "hash")
    assert manager.is_authenticated is True
    await manager.async_clear_credentials()
    assert manager.is_authenticated is False


@pytest.mark.asyncio
async def test_ensure_authenticated_without_credentials_noninteractive(manager):
    assert await manager.ensure_authenticated(interactive=False) is False

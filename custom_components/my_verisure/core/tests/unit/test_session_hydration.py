"""Malformed persisted sessions must recover without provider requests.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import base64
import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def _session() -> dict:
    return {
        "username": "fixture-user",
        "password": "fixture-password",
        "hash_token": "fixture-hash",
        "refresh_token": "fixture-refresh",
        "session_timestamp": time.time(),
        "current_installation": "fixture-installation",
    }


@pytest.mark.parametrize("payload", [None, [], {}, True, 42, "invalid"])
@pytest.mark.asyncio
async def test_non_object_session_preserves_configured_login(tmp_path, payload):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    manager.set_login_credentials("configured-user", "configured-password")
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))

    await manager.async_load_session_from_disk()

    assert manager._session_disk_hydrated is True
    assert manager.username == "configured-user"
    assert manager.password == "configured-password"
    assert manager.hash_token is None
    assert manager.current_installation is None
    assert manager.is_session_valid() is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("username", None),
        ("username", []),
        ("username", " "),
        ("password", None),
        ("password", 123),
        ("password", ""),
        ("hash_token", {}),
        ("hash_token", " "),
        ("refresh_token", []),
        ("refresh_token", ""),
        ("session_timestamp", "invalid"),
        ("session_timestamp", True),
        ("session_timestamp", None),
        ("session_timestamp", 0),
        ("session_timestamp", -1),
        ("session_timestamp", float("nan")),
        ("session_timestamp", float("inf")),
        ("session_timestamp", float("-inf")),
        ("session_timestamp", 10**400),
        ("session_timestamp", time.time() + 86400),
        ("current_installation", {}),
        ("current_installation", []),
        ("current_installation", 123),
        ("current_installation", True),
        ("current_installation", " "),
    ],
)
@pytest.mark.asyncio
async def test_invalid_session_field_is_rejected_atomically(tmp_path, field, value):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    manager.set_login_credentials("configured-user", "configured-password")
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    payload = _session()
    payload[field] = value
    path.write_text(json.dumps(payload))

    await manager.async_load_session_from_disk()

    assert manager._session_disk_hydrated is True
    assert manager.username == "configured-user"
    assert manager.password == "configured-password"
    assert manager.hash_token is None
    assert manager.refresh_token is None
    assert manager.session_timestamp is None
    assert manager.current_installation is None


@pytest.mark.parametrize("contents", [b"\xff", b"{", b"[" * 1500])
@pytest.mark.asyncio
async def test_unreadable_session_is_ignored_without_leaking_content(
    tmp_path, contents
):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    manager.set_login_credentials("configured-user", "configured-password")
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    path.write_bytes(contents)

    await manager.async_load_session_from_disk()

    assert manager._session_disk_hydrated is True
    assert manager.username == "configured-user"
    assert manager.password == "configured-password"
    assert manager.hash_token is None


@pytest.mark.asyncio
async def test_corrupt_session_can_be_replaced_by_normal_authentication(tmp_path):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    manager.set_login_credentials("configured-user", "configured-password")
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    path.write_text("[]")
    token = ".".join(
        base64.urlsafe_b64encode(part).decode().rstrip("=")
        for part in (b"{}", json.dumps({"exp": time.time() + 3600}).encode(), b"sig")
    )

    async def authenticate(username, password):
        await manager.async_update_credentials(username, password, token)
        return SimpleNamespace(success=True)

    authenticate_mock = AsyncMock(side_effect=authenticate)
    manager.set_authenticator(authenticate_mock)

    assert await manager.ensure_authenticated(interactive=False) is True

    authenticate_mock.assert_awaited_once_with("configured-user", "configured-password")
    assert json.loads(path.read_text())["hash_token"] == token


@pytest.mark.asyncio
async def test_corrupt_session_without_configured_credentials_stays_unauthenticated(
    tmp_path,
):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    path.write_text("[]")

    assert await manager.ensure_authenticated(interactive=False) is False
    assert manager.is_authenticated is False


def test_expired_session_keeps_valid_refresh_credentials(tmp_path):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    payload = _session()
    payload["session_timestamp"] = time.time() - 86400
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))

    manager.load_session_sync()

    assert manager.hash_token == "fixture-hash"
    assert manager.refresh_token == "fixture-refresh"
    assert manager.username == "fixture-user"
    assert manager.can_attempt_refresh() is True


def test_session_without_tokens_can_restore_login_only(tmp_path):
    manager = SessionManager(file_manager=FileManager(tmp_path))
    path = Path(manager.session_file)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"username": "fixture-user", "password": "fixture-password"})
    )

    manager.load_session_sync()

    assert manager._session_disk_hydrated is True
    assert manager.username == "fixture-user"
    assert manager.password == "fixture-password"
    assert manager.hash_token is None
    assert manager.is_authenticated is False
    assert manager.can_attempt_refresh() is True

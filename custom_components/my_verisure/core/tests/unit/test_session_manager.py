"""Unit tests for the current SessionManager contract."""

import asyncio
import base64
import json
import threading
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.my_verisure.core.application.models.auth import AuthResult
from ...file_manager import FileManager
from ... import session_manager as session_module
from ...session_manager import SessionManager


@pytest.fixture
def manager(tmp_path):
    value = SessionManager(file_manager=FileManager(tmp_path))
    value.file_manager._ensure_data_directory()
    return value


def test_update_credentials_persists_and_reports_authenticated(manager):
    manager.update_credentials("[REDACTED]", "[REDACTED]", "[REDACTED]", "[REDACTED]")
    assert manager.is_authenticated is True
    assert manager.get_current_hash_token() == "[REDACTED]"
    payload = json.loads(Path(manager.session_file).read_text())
    assert payload["username"] == "[REDACTED]"
    assert payload["password"] == "[REDACTED]"
    assert payload["hash_token"] == "[REDACTED]"




@pytest.mark.asyncio
async def test_transaction_snapshot_restores_memory_and_session_file(manager):
    manager.update_credentials(
        "[REDACTED]", "[REDACTED]", "[REDACTED]", "[REDACTED]"
    )
    snapshot = manager.capture_transaction_state()
    previous_bytes = Path(manager.session_file).read_bytes()

    manager.update_credentials(
        "[REDACTED]", "[REDACTED]", "[REDACTED]", "[REDACTED]"
    )
    await manager.async_restore_transaction_state(snapshot, previous_bytes)

    assert manager.username == "[REDACTED]"
    assert manager.password == "[REDACTED]"
    assert manager.hash_token == "[REDACTED]"
    assert Path(manager.session_file).read_bytes() == previous_bytes



def test_transaction_snapshot_deep_copies_current_installation(manager):
    manager.current_installation = {"nested": {"value": "before"}}
    snapshot = manager.capture_transaction_state()

    manager.current_installation["nested"]["value"] = "after"

    assert snapshot["current_installation"] == {"nested": {"value": "before"}}


def test_update_credentials_rolls_back_on_non_os_error(manager):
    manager.update_credentials(
        "USER_BEFORE", "PASSWORD_BEFORE", "HASH_BEFORE", "REFRESH_BEFORE", persist=False
    )
    previous = (
        manager.username,
        manager.password,
        manager.hash_token,
        manager.refresh_token,
        manager.session_timestamp,
        manager.is_authenticated,
    )

    with patch.object(manager, "_save_session_sync", side_effect=ValueError("serialize")):
        with pytest.raises(ValueError, match="serialize"):
            manager.update_credentials(
                "USER_AFTER", "PASSWORD_AFTER", "HASH_AFTER", "REFRESH_AFTER"
            )

    assert (
        manager.username,
        manager.password,
        manager.hash_token,
        manager.refresh_token,
        manager.session_timestamp,
        manager.is_authenticated,
    ) == previous


@pytest.mark.asyncio
async def test_async_update_credentials_restores_file_after_cancellation(manager):
    previous = {"username": "OLD_USER", "password": "OLD_PASSWORD", "hash_token": "OLD_HASH"}
    Path(manager.session_file).write_text(json.dumps(previous))
    started = threading.Event()
    finished = threading.Event()

    def slow_persist():
        started.set()
        time.sleep(0.05)
        Path(manager.session_file).write_text(json.dumps({"username": "NEW_USER"}))
        finished.set()

    with patch.object(manager, "_persist_session_to_disk_sync", side_effect=slow_persist):
        task = asyncio.create_task(
            manager.async_update_credentials(
                "NEW_USER", "NEW_PASSWORD", "NEW_HASH", "NEW_REFRESH"
            )
        )
        await asyncio.to_thread(started.wait, 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await asyncio.to_thread(finished.wait, 1)

    assert json.loads(Path(manager.session_file).read_text()) == previous


def test_load_session_sync_hydrates_valid_recent_session(manager):
    payload = {
        "username": "[REDACTED]",
        "password": "[REDACTED]",
        "hash_token": "[REDACTED]",
        "refresh_token": "[REDACTED]",
        "session_timestamp": time.time(),
        "current_installation": "[REDACTED]",
    }
    Path(manager.session_file).write_text(json.dumps(payload))
    with patch.object(session_module, "is_jwt_expired", return_value=False):
        manager.load_session_sync()
        assert manager.username == "[REDACTED]"
        assert manager.current_installation == "[REDACTED]"
        assert manager.is_session_valid() is True


def test_clear_credentials_removes_file(manager):
    manager.update_credentials("[REDACTED]", "[REDACTED]", "[REDACTED]")
    manager.clear_credentials()
    assert manager.is_authenticated is False
    assert not Path(manager.session_file).exists()


def test_current_session_data_requires_credentials(manager):
    assert manager.get_current_session_data() is None
    manager.update_credentials("[REDACTED]", "[REDACTED]", "[REDACTED]", persist=False)
    assert manager.get_current_session_data() == {
        "user": "[REDACTED]",
        "login_time": manager.session_timestamp,
    }


def test_expired_session_is_invalid(manager):
    manager.update_credentials("[REDACTED]", "[REDACTED]", "[REDACTED]", persist=False)
    manager.session_timestamp = time.time() - session_module.TOKEN_MAX_AGE_SECONDS - 1
    assert manager.is_session_valid() is False


def test_missing_token_is_invalid(manager):
    manager.username = "user"
    manager.password = "PASSWORD_SENTINEL"
    assert manager.is_session_valid() is False


def test_jwt_validation_error_invalidates_session(manager):
    manager.hash_token = "opaque-token"
    manager.session_timestamp = time.time()
    with patch.object(session_module, "is_jwt_expired", side_effect=ValueError("invalid")):
        assert manager.is_session_valid() is False


def test_service_blocked_cooldown(manager):
    manager.record_service_blocked(60)
    assert manager.is_service_blocked() is True
    manager.clear_service_blocked()
    assert manager.is_service_blocked() is False


@pytest.mark.asyncio
async def test_async_update_and_clear(manager):
    await manager.async_update_credentials("[REDACTED]", "[REDACTED]", "HASH_SENTINEL")
    assert manager.is_authenticated is True
    await manager.async_clear_credentials()
    assert manager.is_authenticated is False


@pytest.mark.asyncio
async def test_async_update_credentials_rolls_back_when_persistence_fails(manager):
    manager.update_credentials(
        "USER_BEFORE", "[REDACTED]", "[REDACTED]", "old-refresh", persist=False
    )
    with patch.object(
        manager,
        "_persist_session_to_disk_sync",
        side_effect=OSError("disk-sentinel"),
    ):
        with pytest.raises(OSError, match="disk-sentinel"):
            await manager.async_update_credentials(
                "USER_AFTER", "[REDACTED]", "VALUE_HASH_AFTER", "VALUE_REFRESH_AFTER"
            )

    assert manager.username == "USER_BEFORE"
    assert manager.hash_token == "[REDACTED]"
    assert manager.is_authenticated is True


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [RuntimeError("write failed"), asyncio.CancelledError()])
async def test_async_update_credentials_rolls_back_on_any_persistence_failure(
    manager, failure
):
    manager.update_credentials(
        "USER_BEFORE", "[REDACTED]", "HASH_BEFORE", "REFRESH_BEFORE", persist=False
    )
    with patch.object(
        manager,
        "async_persist_session_to_disk",
        new=AsyncMock(side_effect=failure),
    ):
        with pytest.raises(type(failure)):
            await manager.async_update_credentials(
                "USER_AFTER", "[REDACTED]", "HASH_AFTER", "REFRESH_AFTER"
            )

    assert manager.username == "USER_BEFORE"
    assert manager.hash_token == "HASH_BEFORE"
    assert manager.refresh_token == "REFRESH_BEFORE"
    assert manager.is_authenticated is True


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [RuntimeError("authentication failed"), asyncio.CancelledError()])
async def test_automatic_reauthentication_preserves_state_on_auth_failure(
    manager, failure
):
    manager._session_disk_hydrated = True
    manager.update_credentials(
        "USER_BEFORE", "[REDACTED]", "HASH_BEFORE", "REFRESH_BEFORE", persist=False
    )
    manager.hash_token = None
    manager._reauthenticator = AsyncMock(side_effect=failure)

    if isinstance(failure, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await manager.ensure_authenticated(interactive=False)
    else:
        assert await manager.ensure_authenticated(interactive=False) is False

    assert manager.username == "USER_BEFORE"
    assert manager.hash_token is None
    assert manager.refresh_token == "REFRESH_BEFORE"




@pytest.mark.asyncio
async def test_automatic_reauthentication_confirms_safe_cleanup_after_rollback_error(
    manager,
):
    manager._session_disk_hydrated = True
    manager.update_credentials(
        "USER_BEFORE", "[REDACTED]", "HASH_BEFORE", "REFRESH_BEFORE", persist=False
    )
    manager.hash_token = None
    manager._reauthenticator = AsyncMock(side_effect=RuntimeError("auth failed"))

    with patch.object(
        manager,
        "async_restore_transaction_state",
        new=AsyncMock(side_effect=RuntimeError("restore failed")),
    ), patch.object(
        manager,
        "async_clear_session_file",
        new=AsyncMock(return_value=True),
    ):
        assert await manager.ensure_authenticated(interactive=False) is False

    assert manager.username is None
    assert manager.password is None
    assert manager.hash_token is None
    assert manager.refresh_token is None
    assert manager.is_authenticated is False


@pytest.mark.asyncio
async def test_automatic_reauthentication_propagates_cancellation_from_rollback(
    manager,
):
    manager._session_disk_hydrated = True
    manager.update_credentials(
        "USER_BEFORE", "[REDACTED]", "HASH_BEFORE", "REFRESH_BEFORE", persist=False
    )
    manager.hash_token = None
    manager._reauthenticator = AsyncMock(side_effect=RuntimeError("auth failed"))

    with patch.object(
        manager,
        "async_restore_transaction_state",
        new=AsyncMock(side_effect=asyncio.CancelledError()),
    ), patch.object(
        manager,
        "async_clear_session_file",
        new=AsyncMock(return_value=True),
    ):
        with pytest.raises(asyncio.CancelledError):
            await manager.ensure_authenticated(interactive=False)


@pytest.mark.asyncio
async def test_automatic_reauthentication_has_single_persistence_owner(manager):
    manager._session_disk_hydrated = True
    valid_token = ".".join(
        base64.urlsafe_b64encode(part).decode().rstrip("=")
        for part in (b"{}", json.dumps({"exp": time.time() + 3600}).encode(), b"sig")
    )
    manager.update_credentials(
        "USER_BEFORE", "PASSWORD_BEFORE", valid_token, "REFRESH_BEFORE", persist=False
    )
    manager.hash_token = None

    async def authenticate(username, password):
        manager.update_credentials(
            username,
            password,
            valid_token,
            "REFRESH_AFTER",
            persist=False,
        )
        return AuthResult(
            success=True,
            message="authenticated",
            hash="HASH_AFTER",
            refresh_token="REFRESH_AFTER",
        )

    manager._reauthenticator = authenticate
    with patch.object(manager, "async_persist_session_to_disk", new=AsyncMock()) as persist:
        assert await manager.ensure_authenticated(interactive=False) is True

    persist.assert_not_awaited()
    assert manager.hash_token == valid_token
    assert manager.refresh_token == "REFRESH_AFTER"


@pytest.mark.asyncio
async def test_ensure_authenticated_without_credentials_noninteractive(manager):
    assert await manager.ensure_authenticated(interactive=False) is False

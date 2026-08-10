"""Session manager injected authentication boundary tests."""

from types import SimpleNamespace

import pytest

from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.asyncio
async def test_session_manager_uses_injected_reauthentication_boundary(tmp_path):
    calls = []

    async def authenticate(username: str, password: str):
        calls.append((username, password))
        return SimpleNamespace(
            success=True,
            hash="hash-token",
            refresh_token="refresh-token",
            message="ok",
        )

    manager = SessionManager(tmp_path / "session.json")
    manager.update_credentials("user", "password", "expired-token", persist=False)
    manager.set_authenticator(authenticate)

    result = await manager._try_automatic_reauthentication()

    assert result is True
    assert calls == [("user", "password")]
    assert manager.hash_token == "hash-token"

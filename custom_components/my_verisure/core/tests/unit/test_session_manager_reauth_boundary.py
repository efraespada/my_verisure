"""Session manager injected authentication boundary tests."""

from __future__ import annotations

import base64
import json
import time
from types import SimpleNamespace

import pytest

from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.asyncio
async def test_session_manager_uses_injected_reauthentication_boundary(tmp_path):
    calls = []

    valid_token = ".".join(
        base64.urlsafe_b64encode(part).decode().rstrip("=")
        for part in (b"{}", json.dumps({"exp": time.time() + 3600}).encode(), b"sig")
    )

    async def authenticate(username: str, password: str):
        calls.append((username, password))
        manager.update_credentials(
            username,
            password,
            valid_token,
            "refresh-token",
            persist=False,
        )
        return SimpleNamespace(
            success=True,
            hash=valid_token,
            refresh_token="refresh-token",
            message="ok",
        )

    manager = SessionManager(
        tmp_path / "data" / "session.json", file_manager=FileManager(tmp_path)
    )
    manager.update_credentials("user", "password", "expired-token", persist=False)
    manager.set_authenticator(authenticate)

    result = await manager._try_automatic_reauthentication()

    assert result is True
    assert calls == [("user", "password")]
    assert manager.hash_token == valid_token

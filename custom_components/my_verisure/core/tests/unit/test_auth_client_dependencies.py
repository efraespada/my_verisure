"""Tests for explicit authentication client dependencies."""

from typing import cast
from types import SimpleNamespace

from custom_components.my_verisure.core.api.auth_client import AuthClient
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def test_auth_client_prefers_entry_scoped_session_manager(tmp_path):
    session_manager = cast(SessionManager, SimpleNamespace())
    device_manager = DeviceManager(FileManager(tmp_path))

    client = AuthClient(
        session_manager=session_manager, device_manager=device_manager
    )

    assert client._resolve_session_manager() is session_manager

"""Tests for explicit authentication client dependencies."""

from types import SimpleNamespace

from custom_components.my_verisure.core.api.auth_client import AuthClient


def test_auth_client_prefers_entry_scoped_session_manager():
    session_manager = SimpleNamespace()

    client = AuthClient(session_manager=session_manager)

    assert client._resolve_session_manager() is session_manager

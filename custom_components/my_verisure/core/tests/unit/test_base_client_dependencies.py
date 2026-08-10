"""Tests for entry-scoped session ownership in the HTTP client base."""

from types import SimpleNamespace

from custom_components.my_verisure.core.api.base_client import BaseClient


def test_base_client_prefers_injected_session_manager():
    session_manager = SimpleNamespace()

    client = BaseClient(session_manager=session_manager)

    assert client._resolve_session_manager() is session_manager

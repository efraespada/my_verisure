"""Tests for entry-scoped session ownership in the HTTP client base."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api.base_client import BaseClient
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
)


def test_base_client_prefers_injected_session_manager():
    session_manager = SimpleNamespace()

    client = BaseClient(session_manager=session_manager)
    assert client._resolve_session_manager() is session_manager


def test_session_headers_require_complete_authenticated_state():
    client = BaseClient(session_manager=SimpleNamespace())

    with pytest.raises(
        MyVerisureAuthenticationError, match="Authenticated session unavailable"
    ):
        client._get_session_headers({}, None)


def test_session_headers_retain_the_configured_spanish_protocol_profile():
    client = BaseClient(session_manager=SimpleNamespace())

    headers = client._get_session_headers({"user": "user"}, "hash")

    assert json.loads(headers["auth"])["lang"] == "es"


async def test_base_client_propagates_cancellation_and_closes_session(monkeypatch):
    class CancelledRequest:
        async def __aenter__(self):
            raise asyncio.CancelledError

        async def __aexit__(self, *_args):
            return False

    session = SimpleNamespace(
        closed=False,
        post=lambda *_args, **_kwargs: CancelledRequest(),
        close=AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.my_verisure.core.api.base_client.aiohttp.ClientSession",
        lambda **_kwargs: session,
    )

    client = BaseClient(session_manager=SimpleNamespace())

    with pytest.raises(asyncio.CancelledError):
        await client._execute_query_direct("query")


async def test_base_client_rejects_non_success_http_status(monkeypatch):
    class Response:
        status = 503

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    session = SimpleNamespace(
        closed=False,
        post=lambda *_args, **_kwargs: Response(),
        close=AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.my_verisure.core.api.base_client.aiohttp.ClientSession",
        lambda **_kwargs: session,
    )

    client = BaseClient(session_manager=SimpleNamespace())
    with pytest.raises(MyVerisureConnectionError, match="HTTP request failed"):
        await client._execute_query_direct("query")

    session.close.assert_awaited_once_with()

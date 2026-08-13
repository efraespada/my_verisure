"""Tests for the coordinator authentication policy."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.coordinator_authentication import (
    CoordinatorAuthenticationPolicy,
)


@pytest.mark.asyncio
async def test_authenticated_decision_does_not_read_cache():
    login = AsyncMock(return_value=True)
    load_cache = Mock()

    result = await CoordinatorAuthenticationPolicy(login, load_cache).authenticate()

    assert result.authenticated is True
    assert result.cached_data is None
    load_cache.assert_not_called()


@pytest.mark.asyncio
async def test_failed_login_returns_cached_snapshot():
    login = AsyncMock(return_value=False)
    cached = {"installation_id": "home-1", "cached": True}
    load_cache = Mock(return_value=cached)

    result = await CoordinatorAuthenticationPolicy(login, load_cache).authenticate()

    assert result.authenticated is False
    assert result.cached_data == cached
    load_cache.assert_called_once_with()


@pytest.mark.asyncio
async def test_failed_login_without_cache_returns_empty_decision():
    login = AsyncMock(return_value=False)
    load_cache = Mock(return_value={})

    result = await CoordinatorAuthenticationPolicy(login, load_cache).authenticate()

    assert result.authenticated is False
    assert result.cached_data is None

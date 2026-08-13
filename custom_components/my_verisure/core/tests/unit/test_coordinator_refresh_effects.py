"""Tests for coordinator refresh side effects."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.coordinator_refresh_effects import (
    CoordinatorRefreshEffects,
)


@pytest.mark.asyncio
async def test_apply_publishes_persists_and_creates_dummy_images() -> None:
    store = Mock()
    store.save = AsyncMock(return_value=True)
    publisher = Mock()
    creator = Mock()
    creator.create_dummy_camera_images = AsyncMock()
    effects = CoordinatorRefreshEffects(store, publisher, creator)
    snapshot = {"installation_id": "home-1"}

    await effects.apply(snapshot, "home-1", create_dummy_images=True)

    publisher.assert_called_once_with(snapshot)
    store.save.assert_awaited_once_with(snapshot)
    creator.create_dummy_camera_images.assert_awaited_once_with("home-1")


@pytest.mark.asyncio
async def test_apply_keeps_persistence_failure_non_fatal() -> None:
    store = Mock()
    store.save = AsyncMock(return_value=False)
    publisher = Mock()
    creator = Mock()
    creator.create_dummy_camera_images = AsyncMock()
    effects = CoordinatorRefreshEffects(store, publisher, creator)

    await effects.apply({"value": 1}, "home-1", create_dummy_images=False)

    publisher.assert_called_once()
    creator.create_dummy_camera_images.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_keeps_dummy_image_failure_non_fatal() -> None:
    store = Mock()
    store.save = AsyncMock(return_value=True)
    publisher = Mock()
    creator = Mock()
    creator.create_dummy_camera_images = AsyncMock(
        side_effect=RuntimeError("camera unavailable")
    )
    effects = CoordinatorRefreshEffects(store, publisher, creator)

    await effects.apply({"value": 1}, "home-1", create_dummy_images=True)

    store.save.assert_awaited_once()

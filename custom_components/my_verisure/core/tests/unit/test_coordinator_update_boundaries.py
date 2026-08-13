"""Focused tests for coordinator session and update error boundaries."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureServiceBlockedError,
)


@pytest.fixture
def coordinator() -> MyVerisureDataUpdateCoordinator:
    value = object.__new__(MyVerisureDataUpdateCoordinator)
    value.installation_id = "home-1"
    value._dev_mode = False
    value.session_manager = Mock()
    value.file_manager = Mock()
    value.snapshot_service = Mock()
    value.create_dummy_camera_images_use_case = Mock()
    value.hass = SimpleNamespace(data={})
    value.data = {}
    setattr(value, "load_alarm_info", Mock(return_value={}))
    setattr(value, "async_login", AsyncMock(return_value=True))
    value.async_set_updated_data = Mock()
    return value


@pytest.mark.asyncio
async def test_update_data_returns_snapshot_and_persists_cache(coordinator) -> None:
    snapshot = {"installation_id": "home-1", "alarm_status": {"status": "armed"}}
    coordinator.snapshot_service.refresh = AsyncMock(return_value=snapshot)
    coordinator.file_manager.async_save_json = AsyncMock(return_value=True)
    coordinator.create_dummy_camera_images_use_case.create_dummy_camera_images = AsyncMock()

    result = await coordinator._async_update_data()

    assert result == snapshot
    coordinator.async_set_updated_data.assert_called_once_with(snapshot)
    coordinator.file_manager.async_save_json.assert_awaited_once()
    coordinator.create_dummy_camera_images_use_case.create_dummy_camera_images.assert_awaited_once_with(
        installation_id="home-1"
    )


@pytest.mark.asyncio
async def test_update_data_uses_cache_when_login_fails(coordinator) -> None:
    cached = {"installation_id": "home-1", "cached": True}
    setattr(coordinator, "async_login", AsyncMock(return_value=False))
    coordinator.load_alarm_info.return_value = cached

    assert await coordinator._async_update_data() == cached


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error, expected",
    [
        (MyVerisureAuthenticationError("bad auth"), ConfigEntryAuthFailed),
        (MyVerisureConnectionError("offline"), UpdateFailed),
    ],
)
async def test_update_data_maps_provider_errors(coordinator, error, expected) -> None:
    coordinator.snapshot_service.refresh = AsyncMock(side_effect=error)

    with pytest.raises(expected):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_update_data_uses_cache_when_service_is_blocked(coordinator) -> None:
    cached = {"installation_id": "home-1", "cached": True}
    coordinator.snapshot_service.refresh = AsyncMock(
        side_effect=MyVerisureServiceBlockedError("blocked")
    )
    coordinator.load_alarm_info.return_value = cached
    coordinator.get_translation = AsyncMock(side_effect=lambda key: key)

    with patch("custom_components.my_verisure.coordinator.async_create") as notify:
        assert await coordinator._async_update_data() == cached

    notify.assert_called_once()

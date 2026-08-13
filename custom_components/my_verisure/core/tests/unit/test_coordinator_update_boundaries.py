"""Focused tests for coordinator session and update error boundaries."""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.application.coordinator_authentication import (
    CoordinatorAuthenticationDecision,
)
from custom_components.my_verisure.core.application.coordinator_failure import (
    CoordinatorFailureClassifier,
)
from custom_components.my_verisure.core.application.coordinator_refresh_effects import (
    CoordinatorRefreshEffects,
)
from custom_components.my_verisure.core.application.coordinator_session_policy import (
    CoordinatorSessionPolicy,
)
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
    value.snapshot_store = Mock()
    value.refresh_effects = Mock(spec=CoordinatorRefreshEffects)
    value.authentication_policy = Mock()
    value._failure_classifier = CoordinatorFailureClassifier()
    value.notifications = Mock()
    value.notifications.notify = AsyncMock()
    value.session_policy = CoordinatorSessionPolicy()
    value.authentication_policy.authenticate = AsyncMock(
        return_value=CoordinatorAuthenticationDecision(authenticated=True)
    )
    value.snapshot_service = Mock()
    value.create_dummy_camera_images_use_case = Mock()
    value.hass = cast(Any, SimpleNamespace(data={}))
    value.data = {}
    setattr(value, "load_alarm_info", Mock(return_value={}))
    setattr(value, "async_login", AsyncMock(return_value=True))
    object.__setattr__(value, "async_set_updated_data", Mock())
    return value


@pytest.mark.asyncio
async def test_update_data_returns_snapshot_and_persists_cache(coordinator) -> None:
    snapshot = {"installation_id": "home-1", "alarm_status": {"status": "armed"}}
    coordinator.snapshot_service.refresh = AsyncMock(return_value=snapshot)
    coordinator.snapshot_store.save = AsyncMock(return_value=True)
    coordinator.create_dummy_camera_images_use_case.create_dummy_camera_images = AsyncMock()

    coordinator.refresh_effects.apply = AsyncMock()

    result = await coordinator._async_update_data()

    coordinator.refresh_effects.apply.assert_awaited_once_with(
        snapshot,
        "home-1",
        create_dummy_images=True,
    )


@pytest.mark.asyncio
async def test_update_data_uses_cache_when_login_fails(coordinator) -> None:
    cached = {"installation_id": "home-1", "cached": True}
    setattr(coordinator, "async_login", AsyncMock(return_value=False))
    coordinator.authentication_policy.authenticate = AsyncMock(
        return_value=CoordinatorAuthenticationDecision(
            authenticated=False, cached_data=cached
        )
    )

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

    coordinator.notifications.notify.assert_awaited_once_with(
        title_key="notifications.service.blocked.title",
        message_key="notifications.service.blocked.message",
        notification_id="verisure_service_blocked",
    )
    notify.assert_not_called()

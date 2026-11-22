"""Contract tests for My Verisure Home Assistant services."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol

from custom_components.my_verisure import services
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.exceptions import (
    MyVerisureAuthenticationError, MyVerisureServiceBlockedError,
)
from custom_components.my_verisure.core.application.models.alarm import ArmResult, DisarmResult
from custom_components.my_verisure.camera import camera_unique_id


def _coordinator(installation_id: str) -> MagicMock:
    coordinator = MagicMock()
    coordinator.config_entry.data = {"installation_id": installation_id}
    coordinator.clear_alarm_transition_state = MagicMock()
    coordinator.clear_button_executing_state = MagicMock()
    coordinator.async_arm_away = AsyncMock(return_value=ArmResult(True, "ok"))
    coordinator.async_arm_home = AsyncMock(return_value=ArmResult(True, "ok"))
    coordinator.async_arm_night = AsyncMock(return_value=ArmResult(True, "ok"))
    coordinator.async_disarm = AsyncMock(return_value=DisarmResult(True, "ok"))
    coordinator.async_request_refresh = AsyncMock()
    coordinator.async_refresh_camera_images = AsyncMock()
    return coordinator


@pytest.mark.asyncio
async def test_all_alarm_handlers_dispatch_to_matching_entry() -> None:
    hass = MagicMock()
    coordinator = _coordinator("installation-1")
    with patch.object(
        services,
        "_iter_coordinators",
        side_effect=lambda _hass: iter((coordinator,)),
    ):
        await services.async_setup_services(hass)
        handlers = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }
        for name in ("arm_away", "arm_home", "arm_night", "disarm"):
            await handlers[name](SimpleNamespace(data={"installation_id": "installation-1"}))

    coordinator.async_arm_away.assert_awaited_once_with()
    coordinator.async_arm_home.assert_awaited_once_with()
    coordinator.async_arm_night.assert_awaited_once_with()
    coordinator.async_disarm.assert_awaited_once_with()
    assert coordinator.clear_alarm_transition_state.call_count == 4


@pytest.mark.asyncio
async def test_get_status_refreshes_only_matching_entry() -> None:
    hass = MagicMock()
    first = _coordinator("first")
    second = _coordinator("second")
    with patch.object(
        services,
        "_iter_coordinators",
        side_effect=lambda _hass: iter((first, second)),
    ):
        await services.async_setup_services(hass)
        handlers = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }
        await handlers["get_status"](SimpleNamespace(data={"installation_id": "second"}))

    first.async_request_refresh.assert_not_awaited()
    second.async_request_refresh.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_refresh_camera_images_clears_button_state_on_failure() -> None:
    hass = MagicMock()
    coordinator = _coordinator("installation-1")
    coordinator.async_refresh_camera_images.side_effect = RuntimeError("transport")
    with patch.object(
        services,
        "_iter_coordinators",
        side_effect=lambda _hass: iter((coordinator,)),
    ):
        await services.async_setup_services(hass)
        handlers = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }
        with pytest.raises(HomeAssistantError, match="Camera image refresh failed"):
            await handlers["refresh_camera_images"](
                SimpleNamespace(data={"installation_id": "installation-1"})
            )

    coordinator.clear_button_executing_state.assert_called_once_with()


@pytest.mark.asyncio
async def test_dispatcher_failure_is_propagated_to_service_caller() -> None:
    hass = MagicMock()
    coordinator = _coordinator("installation-1")
    coordinator.async_arm_away.side_effect = RuntimeError("provider unavailable")
    with patch.object(
        services,
        "_iter_coordinators",
        side_effect=lambda _hass: iter((coordinator,)),
    ):
        await services.async_setup_services(hass)
        handlers = {
            call.args[1]: call.args[2]
            for call in hass.services.async_register.call_args_list
        }
        with pytest.raises(MyVerisureError, match="Alarm command failed"):
            await handlers["arm_away"](SimpleNamespace(data={"installation_id": "installation-1"}))

    coordinator.clear_alarm_transition_state.assert_called_once_with()


def test_service_schemas_reject_empty_or_extra_installation_data() -> None:
    with pytest.raises(vol.Invalid):
        services.SERVICE_ARM_AWAY_SCHEMA({})
    with pytest.raises(vol.Invalid):
        services.SERVICE_DISARM_SCHEMA({"installation_id": "", "unexpected": True})


@pytest.mark.parametrize("error,key", [
    (MyVerisureError("synthetic-sensitive"), "camera_refresh_failed"),
    (MyVerisureAuthenticationError("synthetic-sensitive"), "camera_authentication_required"),
    (MyVerisureServiceBlockedError("synthetic-sensitive"), "camera_service_blocked"),
])
def test_camera_errors_have_safe_home_assistant_translations(error, key):
    public_error = services._camera_refresh_error(error)
    assert isinstance(public_error, HomeAssistantError)
    assert public_error.translation_key == key
    assert public_error.translation_domain == "my_verisure"
    assert "synthetic-sensitive" not in str(public_error)


@pytest.mark.asyncio
@pytest.mark.parametrize("foreign", [False, True])
async def test_camera_selection_is_scoped_to_its_config_entry(foreign):
    hass = MagicMock()
    coordinator = _coordinator("installation-1")
    coordinator.config_entry.entry_id = "entry-1"
    device = {"type": "YR", "code": "2", "name": "Back"}
    coordinator.data = {"detailed_installation": {"installation": {"devices": [device]}}}
    row = SimpleNamespace(
        domain="camera", platform="my_verisure",
        config_entry_id="other-entry" if foreign else "entry-1",
        unique_id=camera_unique_id("entry-1", device),
    )
    with patch.object(services, "_iter_coordinators", side_effect=lambda _: iter((coordinator,))), \
         patch("homeassistant.helpers.entity_registry.async_get", return_value=Mock(async_get=Mock(return_value=row))):
        await services.async_setup_services(hass)
        handler = next(call.args[2] for call in hass.services.async_register.call_args_list if call.args[1] == "refresh_camera_images")
        call = SimpleNamespace(data={"installation_id": "installation-1", "camera_entity_id": "camera.back"})
        if foreign:
            with pytest.raises(HomeAssistantError, match="Selected camera unavailable"):
                await handler(call)
            coordinator.async_refresh_camera_images.assert_not_awaited()
        else:
            await handler(call)
            coordinator.async_refresh_camera_images.assert_awaited_once_with(camera_identifier="YR02")

"""Contract tests for My Verisure Home Assistant services."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol

from custom_components.my_verisure import services
from custom_components.my_verisure.core.api.models.domain.alarm import ArmResult, DisarmResult


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
        await handlers["refresh_camera_images"](
            SimpleNamespace(data={"installation_id": "installation-1"})
        )

    coordinator.clear_button_executing_state.assert_called_once_with()


@pytest.mark.asyncio
async def test_dispatcher_failure_is_reported_without_raising() -> None:
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
        await handlers["arm_away"](SimpleNamespace(data={"installation_id": "installation-1"}))

    coordinator.clear_alarm_transition_state.assert_called_once_with()


def test_service_schemas_reject_empty_or_extra_installation_data() -> None:
    with pytest.raises(vol.Invalid):
        services.SERVICE_ARM_AWAY_SCHEMA({})
    with pytest.raises(vol.Invalid):
        services.SERVICE_DISARM_SCHEMA({"installation_id": "", "unexpected": True})

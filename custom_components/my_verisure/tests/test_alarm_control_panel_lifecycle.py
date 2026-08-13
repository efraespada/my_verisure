"""Lifecycle contracts for the alarm control panel entity."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.alarm_control_panel.const import AlarmControlPanelState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.alarm_control_panel import MyVerisureAlarmControlPanel


def _entity(installation_id: str | None = "installation-1") -> MyVerisureAlarmControlPanel:
    coordinator = MagicMock()
    coordinator.data = None
    coordinator.last_update_success = True
    entry = MockConfigEntry(
        domain="my_verisure",
        title="Test",
        data={} if installation_id is None else {"installation_id": installation_id},
        entry_id="entry-alarm",
    )
    entity = MyVerisureAlarmControlPanel(coordinator, entry)
    entity.hass = MagicMock()
    entity.async_write_ha_state = MagicMock()
    return entity


@pytest.mark.asyncio
async def test_arm_success_clears_transition_state() -> None:
    entity = _entity()
    entity.hass.services.async_call = AsyncMock()

    await entity.async_alarm_arm_away()

    assert entity._transition_state is None
    entity.hass.services.async_call.assert_awaited_once_with(
        "my_verisure", "arm_away", {"installation_id": "installation-1"}
    )


@pytest.mark.asyncio
async def test_disarm_success_clears_transition_state() -> None:
    entity = _entity()
    entity.hass.services.async_call = AsyncMock()

    await entity.async_alarm_disarm()

    assert entity._transition_state is None


@pytest.mark.asyncio
async def test_command_failure_clears_transition_state() -> None:
    entity = _entity()
    entity.hass.services.async_call = AsyncMock(side_effect=RuntimeError("service failed"))

    await entity.async_alarm_arm_home()

    assert entity._transition_state is None
    assert entity.async_write_ha_state.call_count >= 2


@pytest.mark.asyncio
async def test_missing_installation_id_does_not_leave_entity_arming() -> None:
    entity = _entity(None)
    entity.hass.services.async_call = AsyncMock()

    await entity.async_alarm_arm_night()

    entity.hass.services.async_call.assert_not_awaited()
    assert entity._transition_state is None


def test_available_uses_coordinator_health() -> None:
    entity = _entity()
    entity.coordinator.last_update_success = False

    assert entity.available is False

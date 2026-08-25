"""Lifecycle contracts for the alarm control panel entity."""

import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.alarm_control_panel import MyVerisureAlarmControlPanel
from custom_components.my_verisure.core.application.exceptions import MyVerisureError


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
    object.__setattr__(entity, "hass", MagicMock())
    state_writer = MagicMock()
    object.__setattr__(entity, "async_write_ha_state", state_writer)
    cast(Any, entity)._state_writer = state_writer
    return entity


@pytest.mark.asyncio
async def test_arm_success_clears_transition_state() -> None:
    entity = _entity()
    service_call = AsyncMock()
    object.__setattr__(entity.hass.services, "async_call", service_call)

    await entity.async_alarm_arm_away()

    assert entity._transition_state is None
    service_call.assert_awaited_once_with(
        "my_verisure", "arm_away", {"installation_id": "installation-1"}
    )


@pytest.mark.asyncio
async def test_disarm_success_clears_transition_state() -> None:
    entity = _entity()
    service_call = AsyncMock()
    object.__setattr__(entity.hass.services, "async_call", service_call)

    await entity.async_alarm_disarm()

    assert entity._transition_state is None


@pytest.mark.asyncio
async def test_command_failure_clears_transition_state() -> None:
    entity = _entity()
    object.__setattr__(entity.hass.services, "async_call", AsyncMock(side_effect=RuntimeError("service failed")))

    with pytest.raises(MyVerisureError, match="Alarm command failed"):
        await entity.async_alarm_arm_home()

    assert entity._transition_state is None
    assert cast(Any, entity)._state_writer.call_count >= 2




@pytest.mark.asyncio
async def test_domain_command_failure_is_propagated() -> None:
    entity = _entity()
    object.__setattr__(
        entity.hass.services,
        "async_call",
        AsyncMock(side_effect=MyVerisureError("Alarm command failed")),
    )

    with pytest.raises(MyVerisureError, match="Alarm command failed"):
        await entity.async_alarm_arm_home()

    assert entity._transition_state is None




@pytest.mark.asyncio
async def test_cancelled_command_clears_transition_state_and_propagates() -> None:
    entity = _entity()
    object.__setattr__(
        entity.hass.services,
        "async_call",
        AsyncMock(side_effect=asyncio.CancelledError),
    )

    with pytest.raises(asyncio.CancelledError):
        await entity.async_alarm_arm_home()

    assert entity._transition_state is None


@pytest.mark.asyncio
async def test_missing_installation_id_does_not_leave_entity_arming() -> None:
    entity = _entity(None)
    service_call = AsyncMock()
    object.__setattr__(entity.hass.services, "async_call", service_call)

    with pytest.raises(MyVerisureError, match="Installation not found"):
        await entity.async_alarm_arm_night()

    service_call.assert_not_awaited()
    assert entity._transition_state is None


def test_available_uses_coordinator_health() -> None:
    entity = _entity()
    entity.coordinator.last_update_success = False

    assert entity.available is False

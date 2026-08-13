"""Behavior tests for Home Assistant adapter boundaries."""

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure import integration, services
from custom_components.my_verisure.sensor import (
    MyVerisureActiveAlarmsSensor,
    MyVerisureAlarmStatusSensor,
    MyVerisureLastUpdatedSensor,
    MyVerisurePanelStateSensor,
)


@pytest.fixture
def config_entry() -> ConfigEntry:
    return MockConfigEntry(
        version=1,
        minor_version=1,
        domain="my_verisure",
        title="Test",
        data={"installation_id": "123"},
        source="test",
        entry_id="entry-1",
    )


def _coordinator(data=None, success=True) -> Any:
    return SimpleNamespace(data=data, last_update_success=success)


def _alarm_data(day=False, night=False, total=False, external=False):
    return {
        "alarm_status": {
            "data": {
                "internal": {
                    "day": {"status": day},
                    "night": {"status": night},
                    "total": {"status": total},
                },
                "external": {"status": external},
            }
        }
    }


def test_alarm_status_sensor_maps_alarm_state_and_attributes(config_entry):
    coordinator = _coordinator(
        _alarm_data(total=True, external=True)
    )
    sensor = MyVerisureAlarmStatusSensor(coordinator, config_entry, "alarm", "Alarm")

    assert sensor.native_value == "Total and Perimeter Active"
    assert sensor.extra_state_attributes["internal_total_status"] is True
    assert sensor.available is True


def test_active_alarms_sensor_reports_multiple_states(config_entry):
    coordinator = _coordinator(_alarm_data(day=True, external=True))
    sensor = MyVerisureActiveAlarmsSensor(coordinator, config_entry, "active", "Active")

    assert sensor.native_value == "Multiple (2)"
    assert sensor.extra_state_attributes["active_alarms"] == [
        "Internal Day",
        "External",
    ]


def test_sensors_handle_missing_data(config_entry):
    coordinator = _coordinator(None, success=False)
    alarm = MyVerisureAlarmStatusSensor(coordinator, config_entry, "alarm", "Alarm")
    active = MyVerisureActiveAlarmsSensor(coordinator, config_entry, "active", "Active")
    last = MyVerisureLastUpdatedSensor(coordinator, config_entry, "last", "Last")
    panel = MyVerisurePanelStateSensor(coordinator, config_entry, "panel", "Panel")

    assert alarm.native_value is None
    assert active.native_value == "Sin datos"
    assert last.native_value is None
    assert panel.native_value == "unavailable"
    assert alarm.available is False
    assert active.available is False


def test_disarm_schema_rejects_unsupported_code(config_entry):
    with pytest.raises(vol.Invalid):
        services.SERVICE_DISARM_SCHEMA(
            {"installation_id": "123", "code": "2468"}
        )


def test_last_updated_sensor_reads_timestamp(config_entry):
    timestamp = datetime.now(timezone.utc)
    sensor = MyVerisureLastUpdatedSensor(
        _coordinator({"last_updated": timestamp.timestamp()}),
        config_entry,
        "last",
        "Last",
    )

    assert sensor.native_value == timestamp


@pytest.mark.asyncio
async def test_services_register_and_unload_all_handlers():
    hass = MagicMock()
    await services.async_setup_services(hass)

    registered = [call.args[1] for call in hass.services.async_register.call_args_list]
    assert registered == [
        "arm_away",
        "arm_home",
        "arm_night",
        "disarm",
        "get_status",
        "refresh_camera_images",
    ]

    await services.async_unload_services(hass)
    removed = [call.args[1] for call in hass.services.async_remove.call_args_list]
    assert removed == registered


@pytest.mark.asyncio
async def test_integration_setup_initializes_domain_data():
    hass = MagicMock()
    hass.data = {}

    assert await integration.async_setup(hass, {}) is True
    assert "my_verisure" in hass.data


@pytest.mark.asyncio
async def test_integration_unload_last_entry_removes_services(config_entry):
    hass = MagicMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
    hass.config_entries.async_entries.return_value = [config_entry]
    hass.data = {"my_verisure": {"services_setup": True}}

    with patch.object(
        integration,
        "async_unload_services",
        new_callable=AsyncMock,
    ) as unload_services:
        assert await integration.async_unload_entry(hass, config_entry) is True

    unload_services.assert_awaited_once_with(hass)
    assert "my_verisure" not in hass.data

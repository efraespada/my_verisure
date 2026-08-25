"""Platform for My Verisure sensors."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.application.alarm_state import AlarmState, analyze_alarm_state
from .core.const import LOGGER, ENTITY_NAMES
from .coordinator import MyVerisureDataUpdateCoordinator
from .device import get_device_info


def _alarm_snapshot(coordinator: MyVerisureDataUpdateCoordinator):
    """Analyze coordinator alarm data without inventing an inactive state."""
    if not coordinator.data:
        return None
    alarm_status = coordinator.data.get("alarm_status")
    if not isinstance(alarm_status, dict):
        return None
    return analyze_alarm_state(alarm_status)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up My Verisure sensors based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = config_entry.runtime_data

    entities = []

    # Create alarm status sensors
    entities.extend([
        # General Alarm Status Sensor
        MyVerisureAlarmStatusSensor(
            coordinator,
            config_entry,
            "alarm_status",
            ENTITY_NAMES["sensor_alarm_status"],
        ),
        # Active Alarms Sensor
        MyVerisureActiveAlarmsSensor(
            coordinator,
            config_entry,
            "active_alarms",
            ENTITY_NAMES["sensor_active_alarms"],
        ),
        # Panel State Sensor (for automations)
        MyVerisurePanelStateSensor(
            coordinator,
            config_entry,
            "panel_state",
            ENTITY_NAMES["sensor_panel_state"],
        ),
        # Last Updated Sensor
        MyVerisureLastUpdatedSensor(
            coordinator,
            config_entry,
            "last_updated",
            ENTITY_NAMES["sensor_last_updated"],
        ),
    ])

    async_add_entities(entities)


class MyVerisureAlarmStatusSensor(SensorEntity):
    """Representation of My Verisure alarm status sensor."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_id: str,
        friendly_name: str,
    ) -> None:
        """Initialize the alarm status sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.sensor_id = sensor_id
        
        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_id}"
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_should_poll = False
        
        # Set device info
        self._attr_device_info = get_device_info(config_entry)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        snapshot = _alarm_snapshot(self.coordinator)
        if snapshot is None or snapshot.state is AlarmState.UNKNOWN:
            return None
        labels = {
            AlarmState.ARMED_AWAY: "Total Internal Active",
            AlarmState.ARMED_NIGHT: "Internal Night Active",
            AlarmState.ARMED_HOME: "Internal Day Active",
            AlarmState.DISARMED: "Alarm Disarmed",
        }
        active = snapshot.active_alarms
        if len(active) > 1 and snapshot.external:
            return "Total and Perimeter Active" if snapshot.internal_total else f"{active[0]} and Perimeter Active"
        return labels[snapshot.state]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        snapshot = _alarm_snapshot(self.coordinator)
        if snapshot is None or snapshot.state is AlarmState.UNKNOWN:
            return {}
        return {
            "internal_day_status": snapshot.internal_day,
            "internal_night_status": snapshot.internal_night,
            "internal_total_status": snapshot.internal_total,
            "external_status": snapshot.external,
        }
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class MyVerisureActiveAlarmsSensor(SensorEntity):
    """Representation of My Verisure active alarms sensor."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_id: str,
        friendly_name: str,
    ) -> None:
        """Initialize the active alarms sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.sensor_id = sensor_id
        
        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_id}"
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_should_poll = False
        
        # Set device info
        self._attr_device_info = get_device_info(config_entry)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        snapshot = _alarm_snapshot(self.coordinator)
        if snapshot is None or snapshot.state is AlarmState.UNKNOWN:
            return None
        active_alarms = list(snapshot.active_alarms)
        if not active_alarms:
            return "Disarmed"
        if len(active_alarms) == 1:
            return active_alarms[0]
        return f"Multiple ({len(active_alarms)})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return {}

        snapshot = _alarm_snapshot(self.coordinator)
        if snapshot is None or snapshot.state is AlarmState.UNKNOWN:
            return {}

        active_alarms = list(snapshot.active_alarms)
        internal_day = snapshot.internal_day
        internal_night = snapshot.internal_night
        internal_total = snapshot.internal_total
        external_status = snapshot.external
        
        return {
            "active_alarms": active_alarms,
            "alarm_count": len(active_alarms),
            "internal_day_active": internal_day,
            "internal_night_active": internal_night,
            "internal_total_active": internal_total,
            "external_active": external_status,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class MyVerisureLastUpdatedSensor(SensorEntity):
    """Representation of My Verisure last updated sensor."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_id: str,
        friendly_name: str,
    ) -> None:
        """Initialize the last updated sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.sensor_id = sensor_id
        
        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_id}"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_state_class = None
        self._attr_should_poll = False
        
        # Set device info
        self._attr_device_info = get_device_info(config_entry)

    @property
    def native_value(self) -> datetime | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        last_updated = self.coordinator.data.get("last_updated")
        if last_updated is None:
            return None

        try:
            # Convertir timestamp a datetime
            result = datetime.fromtimestamp(last_updated, timezone.utc)
            return result
        except (ValueError, TypeError):
            LOGGER.error("LastUpdatedSensor: Error converting timestamp")
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        last_updated = self.coordinator.data.get("last_updated")
        
        return {
            "timestamp": last_updated,
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        ) 


class MyVerisurePanelStateSensor(SensorEntity):
    """Representation of My Verisure panel state sensor for automations."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_id: str,
        friendly_name: str,
    ) -> None:
        """Initialize the panel state sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.sensor_id = sensor_id
        
        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_id}"
        self._attr_device_class = None
        self._attr_state_class = None
        self._attr_should_poll = False
        
        # Set device info
        self._attr_device_info = get_device_info(config_entry)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        snapshot = _alarm_snapshot(self.coordinator)
        if snapshot is None or snapshot.state is AlarmState.UNKNOWN:
            return None
        return snapshot.state.value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        snapshot = _alarm_snapshot(self.coordinator)
        if snapshot is None or snapshot.state is AlarmState.UNKNOWN:
            return {}
        return {
            "internal_day_status": snapshot.internal_day,
            "internal_night_status": snapshot.internal_night,
            "internal_total_status": snapshot.internal_total,
            "external_status": snapshot.external,
        }
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        ) 
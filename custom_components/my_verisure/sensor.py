"""Platform for My Verisure sensors."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
import math

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTime
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .core.application.alarm_state import AlarmState, analyze_alarm_state
from .core.application.notifications import BINDING_STATES
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

    if getattr(coordinator, "notification_hub", None) is not None:
        entities.extend(
            MyVerisureNotificationDiagnosticSensor(coordinator, config_entry, key)
            for key in (
                "last_received", "last_accepted", "last_verified",
                "binding_state", "cooldown_remaining",
            )
        )
    async_add_entities(entities)


class MyVerisureNotificationDiagnosticSensor(SensorEntity):
    """Read a typed local summary without polling the provider or hiding events."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self, coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry, key: str,
    ) -> None:
        self._coordinator = coordinator
        self._key = key
        self._diagnostics_active = False
        self._cooldown_cancel: CALLBACK_TYPE | None = None
        self._attr_unique_id = f"{config_entry.entry_id}_push_{key}"
        self._attr_translation_key = f"push_{key}"
        self._attr_device_info = get_device_info(config_entry)
        if key == "binding_state":
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(BINDING_STATES)
        elif key == "cooldown_remaining":
            self._attr_device_class = SensorDeviceClass.DURATION
            self._attr_native_unit_of_measurement = UnitOfTime.SECONDS
        else:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> datetime | float | str | None:
        value = self._coordinator.notification_diagnostics().get(self._key)
        if self._key == "binding_state":
            return value if isinstance(value, str) and value in BINDING_STATES else None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        if not math.isfinite(value):
            return None
        if self._key == "cooldown_remaining":
            return float(value) if value >= 0 else None
        try:
            return dt_util.utc_from_timestamp(value)
        except (ValueError, OverflowError, OSError):
            return None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._diagnostics_active = True
        self.async_on_remove(self._shutdown_diagnostics)
        self.async_on_remove(
            self._coordinator.notification_hub.subscribe_diagnostics(self._updated)
        )
        self._schedule_cooldown_update()

    @callback
    def _updated(self) -> None:
        if not self._diagnostics_active:
            return
        self.async_write_ha_state()
        self._schedule_cooldown_update()

    @callback
    def _schedule_cooldown_update(self) -> None:
        if self._key != "cooldown_remaining" or not self._diagnostics_active:
            return
        if self._cooldown_cancel is not None:
            self._cooldown_cancel()
        remaining = self.native_value
        delay = (
            min(30.0, max(0.05, remaining))
            if isinstance(remaining, float) and remaining > 0
            else 30.0
        )
        self._cooldown_cancel = async_call_later(self.hass, delay, self._cooldown_tick)

    @callback
    def _cooldown_tick(self, _now: datetime) -> None:
        self._cooldown_cancel = None
        self._updated()

    @callback
    def _shutdown_diagnostics(self) -> None:
        self._diagnostics_active = False
        if self._cooldown_cancel is not None:
            self._cooldown_cancel()
            self._cooldown_cancel = None


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
        if active == ("External",):
            return "Perimeter Active"
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

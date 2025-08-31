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

from .const import DOMAIN, LOGGER, ENTITY_NAMES
from .coordinator import MyVerisureDataUpdateCoordinator
from .device import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up My Verisure sensors based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

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
        if not self.coordinator.data:
            return None

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return "Desconocido"

        # Analizar el estado de la alarma
        internal = alarm_status.get("internal", {})
        external = alarm_status.get("external", {})
        
        # Determinar el estado general
        internal_day = internal.get("day", {}).get("status", False)
        internal_night = internal.get("night", {}).get("status", False)
        internal_total = internal.get("total", {}).get("status", False)
        external_status = external.get("status", False)
        
        if internal_total and external_status:
            return "Total and Perimeter Active"
        elif internal_total:
            return "Total Internal Active"
        elif internal_day and external_status:
            return "Internal Day and Perimeter Active"
        elif internal_day:
            return "Internal Day Active"
        elif internal_night:
            return "Internal Night Active"
        elif internal_night and external_status:
            return "Internal Night and Perimeter Active"
        elif external_status:
            return "Perimeter Active"
        else:
            return "Alarm Disarmed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return {}

        internal = alarm_status.get("internal", {})
        external = alarm_status.get("external", {})
        
        return {
            "internal_day_status": internal.get("day", {}).get("status", False),
            "internal_night_status": internal.get("night", {}).get("status", False),
            "internal_total_status": internal.get("total", {}).get("status", False),
            "external_status": external.get("status", False),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
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
        if not self.coordinator.data:
            return "Sin datos"

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return "Desconectado"

        # Analizar el estado de la alarma
        internal = alarm_status.get("internal", {})
        external = alarm_status.get("external", {})
        
        # Determinar qué alarmas están activas
        active_alarms = []
        
        internal_day = internal.get("day", {}).get("status", False)
        internal_night = internal.get("night", {}).get("status", False)
        internal_total = internal.get("total", {}).get("status", False)
        external_status = external.get("status", False)
        
        if internal_total:
            active_alarms.append("Internal Total")
        if internal_day:
            active_alarms.append("Internal Day")
        if internal_night:
            active_alarms.append("Internal Night")
        if external_status:
            active_alarms.append("External")
        
        if not active_alarms:
            return "Disarmed"
        elif len(active_alarms) == 1:
            return active_alarms[0]
        else:
            return f"Multiple ({len(active_alarms)})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return {}

        # Analyze alarm state
        internal = alarm_status.get("internal", {})
        external = alarm_status.get("external", {})
        
        # Determine which alarms are active
        active_alarms = []
        
        internal_day = internal.get("day", {}).get("status", False)
        internal_night = internal.get("night", {}).get("status", False)
        internal_total = internal.get("total", {}).get("status", False)
        external_status = external.get("status", False)
        
        if internal_total:
            active_alarms.append("Internal Total")
        if internal_day:
            active_alarms.append("Internal Day")
        if internal_night:
            active_alarms.append("Internal Night")
        if external_status:
            active_alarms.append("External")
        
        return {
            "active_alarms": active_alarms,
            "alarm_count": len(active_alarms),
            "internal_day_active": internal_day,
            "internal_night_active": internal_night,
            "internal_total_active": internal_total,
            "external_active": external_status,
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
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
        except (ValueError, TypeError) as e:
            LOGGER.error("LastUpdatedSensor: Error converting timestamp %s: %s", last_updated, e)
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        last_updated = self.coordinator.data.get("last_updated")
        
        return {
            "timestamp": last_updated,
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
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
        if not self.coordinator.data:
            return "unavailable"

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return "disarmed"

        # Analizar el estado de la alarma usando la misma lógica que el panel
        internal = alarm_status.get("internal", {})
        external = alarm_status.get("external", {})
        
        # Determinar el estado principal basado en prioridad
        internal_day = internal.get("day", {}).get("status", False)
        internal_night = internal.get("night", {}).get("status", False)
        internal_total = internal.get("total", {}).get("status", False)
        external_status = external.get("status", False)
        
        # Prioridad: Total > Night > Day > External > Disarmed
        if internal_total:
            return "armed_away"
        elif internal_night:
            return "armed_night"
        elif internal_day:
            return "armed_home"
        elif external_status:
            return "armed_home"  # Map external to home
        else:
            return "disarmed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return {}

        internal = alarm_status.get("internal", {})
        external = alarm_status.get("external", {})
        
        return {
            "internal_day_status": internal.get("day", {}).get("status", False),
            "internal_night_status": internal.get("night", {}).get("status", False),
            "internal_total_status": internal.get("total", {}).get("status", False),
            "external_status": external.get("status", False),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
            "entity_id": f"alarm_control_panel.my_verisure_alarm_{self.config_entry.data.get('installation_id', 'unknown')}",
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
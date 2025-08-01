"""Platform for My Verisure sensors."""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator


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
        # Sensor de Estado General de Alarma
        MyVerisureAlarmStatusSensor(
            coordinator,
            config_entry,
            "alarm_status",
            "Estado General de Alarma",
        ),
        # Sensor de Última Actualización
        MyVerisureLastUpdatedSensor(
            coordinator,
            config_entry,
            "last_updated",
            "Última Actualización",
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
            return "Alarma Total Activa"
        elif internal_total:
            return "Alarma Interna Total Activa"
        elif internal_day and external_status:
            return "Alarma Interna y Perimetral Activa"
        elif internal_day:
            return "Alarma Interna Día Activa"
        elif internal_night:
            return "Alarma Interna Noche Activa"
        elif internal_night and external_status:
            return "Alarma Interna y Perimetral Noche Activa"
        elif external_status:
            return "Alarma Perimetral Activa"
        else:
            return "Alarma Desactivada"

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
            return datetime.fromtimestamp(last_updated)
        except (ValueError, TypeError):
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
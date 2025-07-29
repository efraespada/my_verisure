"""Platform for My Verisure sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator

# Device type to sensor configuration mapping
DEVICE_TYPE_TO_SENSOR_CONFIG = {
    "TEMPERATURE": {
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": UnitOfTemperature.CELSIUS,
        "friendly_name": "Temperature",
    },
    "HUMIDITY": {
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": PERCENTAGE,
        "friendly_name": "Humidity",
    },
    "BATTERY": {
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": PERCENTAGE,
        "friendly_name": "Battery",
    },
    "SIGNAL": {
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit_of_measurement": "dBm",
        "friendly_name": "Signal Strength",
    },
}


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

    # Get climate sensors (temperature, humidity)
    climate_devices = coordinator.data.get("climate", {})
    for device_id, device_data in climate_devices.items():
        device_type = device_data.get("type", "UNKNOWN")
        
        # Create temperature sensor if available
        if "TEMPERATURE" in device_type or "TEMP" in device_type:
            entities.append(
                MyVerisureSensor(
                    coordinator,
                    config_entry,
                    device_id,
                    device_data,
                    "TEMPERATURE",
                    f"Temperature {device_id}",
                )
            )
        
        # Create humidity sensor if available
        if "HUMIDITY" in device_type or "HUM" in device_type:
            entities.append(
                MyVerisureSensor(
                    coordinator,
                    config_entry,
                    device_id,
                    device_data,
                    "HUMIDITY",
                    f"Humidity {device_id}",
                )
            )

    # Get battery and signal sensors from all devices
    all_devices = {}
    all_devices.update(coordinator.data.get("door_window", {}))
    all_devices.update(coordinator.data.get("sensors", {}))
    all_devices.update(coordinator.data.get("climate", {}))
    
    for device_id, device_data in all_devices.items():
        # Create battery sensor if battery level is available
        if "battery" in device_data:
            entities.append(
                MyVerisureSensor(
                    coordinator,
                    config_entry,
                    device_id,
                    device_data,
                    "BATTERY",
                    f"Battery {device_id}",
                )
            )
        
        # Create signal sensor if signal strength is available
        if "signal" in device_data:
            entities.append(
                MyVerisureSensor(
                    coordinator,
                    config_entry,
                    device_id,
                    device_data,
                    "SIGNAL",
                    f"Signal {device_id}",
                )
            )

    async_add_entities(entities)


class MyVerisureSensor(SensorEntity):
    """Representation of a My Verisure sensor."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
        sensor_type: str,
        friendly_name: str,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.device_id = device_id
        self.device_data = device_data
        self.sensor_type = sensor_type
        
        # Get sensor configuration
        config = DEVICE_TYPE_TO_SENSOR_CONFIG.get(sensor_type, {})
        self._attr_device_class = config.get("device_class")
        self._attr_state_class = config.get("state_class")
        self._attr_native_unit_of_measurement = config.get("unit_of_measurement")
        
        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_{device_id}_{sensor_type.lower()}"
        self._attr_should_poll = False

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        # Get the latest device data
        device_data = self._get_device_data()
        if not device_data:
            return None

        # Extract value based on sensor type
        if self.sensor_type == "TEMPERATURE":
            value = device_data.get("temperature")
            if value is not None:
                # Convert to Celsius if needed
                unit = device_data.get("temperature_unit", "C")
                if unit.upper() == "F":
                    value = (value - 32) * 5 / 9
                return round(value, 1)
        
        elif self.sensor_type == "HUMIDITY":
            value = device_data.get("humidity")
            if value is not None:
                return round(value, 1)
        
        elif self.sensor_type == "BATTERY":
            value = device_data.get("battery")
            if value is not None:
                return round(value, 0)
        
        elif self.sensor_type == "SIGNAL":
            value = device_data.get("signal")
            if value is not None:
                return round(value, 1)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        device_data = self._get_device_data()
        if not device_data:
            return {}

        return {
            "device_id": self.device_id,
            "device_type": device_data.get("type", "Unknown"),
            "sensor_type": self.sensor_type,
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
        }

    def _get_device_data(self) -> dict[str, Any] | None:
        """Get the current device data from coordinator."""
        if not self.coordinator.data:
            return None

        # Look in all device categories
        for category in ["door_window", "sensors", "climate"]:
            devices = self.coordinator.data.get(category, {})
            if self.device_id in devices:
                return devices[self.device_id]

        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self._get_device_data() is not None

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        ) 
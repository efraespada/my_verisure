"""Platform for My Verisure binary sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator

# Device type to device class mapping
DEVICE_TYPE_TO_CLASS = {
    "PIR": BinarySensorDeviceClass.MOTION,
    "DOOR": BinarySensorDeviceClass.DOOR,
    "WINDOW": BinarySensorDeviceClass.WINDOW,
    "SMOKE": BinarySensorDeviceClass.SMOKE,
    "WATER": BinarySensorDeviceClass.MOISTURE,
    "GLASS": BinarySensorDeviceClass.SOUND,
    "VIBRATION": BinarySensorDeviceClass.VIBRATION,
    "GAS": BinarySensorDeviceClass.GAS,
    "HEAT": BinarySensorDeviceClass.HEAT,
    "MOTION": BinarySensorDeviceClass.MOTION,
    "OCCUPANCY": BinarySensorDeviceClass.OCCUPANCY,
    "OPENING": BinarySensorDeviceClass.OPENING,
    "PRESENCE": BinarySensorDeviceClass.PRESENCE,
    "SIREN": BinarySensorDeviceClass.SOUND,
    "TAMPER": BinarySensorDeviceClass.TAMPER,
}

# Device type to friendly name mapping
DEVICE_TYPE_TO_NAME = {
    "PIR": "Motion Detector",
    "DOOR": "Door Sensor",
    "WINDOW": "Window Sensor",
    "SMOKE": "Smoke Detector",
    "WATER": "Water Leak Detector",
    "GLASS": "Glass Break Detector",
    "VIBRATION": "Vibration Sensor",
    "GAS": "Gas Detector",
    "HEAT": "Heat Detector",
    "MOTION": "Motion Sensor",
    "OCCUPANCY": "Occupancy Sensor",
    "OPENING": "Opening Sensor",
    "PRESENCE": "Presence Sensor",
    "SIREN": "Siren",
    "TAMPER": "Tamper Sensor",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up My Verisure binary sensors based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = []

    # Get door/window sensors
    door_window_devices = coordinator.data.get("door_window", {})
    for device_id, device_data in door_window_devices.items():
        device_type = device_data.get("type", "UNKNOWN")
        device_class = DEVICE_TYPE_TO_CLASS.get(device_type, BinarySensorDeviceClass.OPENING)
        
        entities.append(
            MyVerisureBinarySensor(
                coordinator,
                config_entry,
                device_id,
                device_data,
                device_class,
                f"{DEVICE_TYPE_TO_NAME.get(device_type, device_type)} {device_id}",
            )
        )

    # Get motion sensors
    motion_devices = coordinator.data.get("sensors", {})
    for device_id, device_data in motion_devices.items():
        device_type = device_data.get("type", "UNKNOWN")
        if device_type in ["PIR", "MOTION"]:
            device_class = BinarySensorDeviceClass.MOTION
            entities.append(
                MyVerisureBinarySensor(
                    coordinator,
                    config_entry,
                    device_id,
                    device_data,
                    device_class,
                    f"Motion Detector {device_id}",
                )
            )

    async_add_entities(entities)


class MyVerisureBinarySensor(BinarySensorEntity):
    """Representation of a My Verisure binary sensor."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
        device_class: BinarySensorDeviceClass,
        friendly_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.device_id = device_id
        self.device_data = device_data
        self._attr_device_class = device_class
        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_{device_id}"
        self._attr_should_poll = False

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None

        # Get the latest device data
        device_data = self._get_device_data()
        if not device_data:
            return None

        # Check if device is triggered/active
        status = device_data.get("status", "UNKNOWN")
        is_active = device_data.get("active", False)
        
        LOGGER.warning("Binary sensor %s: status=%s, active=%s", 
                      self.device_id, status, is_active)
        
        # Consider device "on" if it's triggered or active
        return status.upper() in ["TRIGGERED", "ACTIVE", "OPEN", "MOTION"] or is_active

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        device_data = self._get_device_data()
        if not device_data:
            return {}

        return {
            "device_id": self.device_id,
            "device_type": device_data.get("type", "Unknown"),
            "status": device_data.get("status", "Unknown"),
            "active": device_data.get("active", False),
            "battery_level": device_data.get("battery", None),
            "signal_strength": device_data.get("signal", None),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
        }

    def _get_device_data(self) -> dict[str, Any] | None:
        """Get the current device data from coordinator."""
        if not self.coordinator.data:
            return None

        # Look in door_window devices
        door_window_devices = self.coordinator.data.get("door_window", {})
        if self.device_id in door_window_devices:
            return door_window_devices[self.device_id]

        # Look in sensors
        sensors = self.coordinator.data.get("sensors", {})
        if self.device_id in sensors:
            return sensors[self.device_id]

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
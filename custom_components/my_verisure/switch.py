"""Platform for My Verisure switches."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up My Verisure switches based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = []

    # Get smart plugs
    smart_plugs = coordinator.data.get("smart_plugs", {})
    for device_id, device_data in smart_plugs.items():
        entities.append(
            MyVerisureSwitch(
                coordinator,
                config_entry,
                device_id,
                device_data,
            )
        )

    async_add_entities(entities)


class MyVerisureSwitch(SwitchEntity):
    """Representation of a My Verisure switch."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.device_id = device_id
        self.device_data = device_data
        self._attr_name = f"Smart Plug {device_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_{device_id}"
        self._attr_should_poll = False

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        if not self.coordinator.data:
            return None

        device_data = self._get_device_data()
        if not device_data:
            return None

        status = device_data.get("status", "UNKNOWN")
        is_active = device_data.get("active", False)
        
        LOGGER.warning("Switch %s: status=%s, active=%s", 
                      self.device_id, status, is_active)
        
        return status.upper() in ["ON", "ACTIVE"] or is_active

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
            "power_consumption": device_data.get("power_consumption", None),
            "battery_level": device_data.get("battery", None),
            "signal_strength": device_data.get("signal", None),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
        }

    def _get_device_data(self) -> dict[str, Any] | None:
        """Get the current device data from coordinator."""
        if not self.coordinator.data:
            return None

        smart_plugs = self.coordinator.data.get("smart_plugs", {})
        return smart_plugs.get(self.device_id)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        LOGGER.warning("Turning on switch %s", self.device_id)
        # TODO: Implement actual turn on command to My Verisure API
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        LOGGER.warning("Turning off switch %s", self.device_id)
        # TODO: Implement actual turn off command to My Verisure API
        await self.coordinator.async_request_refresh()

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
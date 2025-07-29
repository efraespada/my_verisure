"""Platform for My Verisure locks."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity, LockEntityFeature
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
    """Set up My Verisure locks based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = []

    # Get locks
    locks = coordinator.data.get("locks", {})
    for device_id, device_data in locks.items():
        entities.append(
            MyVerisureLock(
                coordinator,
                config_entry,
                device_id,
                device_data,
            )
        )

    async_add_entities(entities)


class MyVerisureLock(LockEntity):
    """Representation of a My Verisure lock."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the lock."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.device_id = device_id
        self.device_data = device_data
        self._attr_name = f"Lock {device_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_{device_id}"
        self._attr_supported_features = LockEntityFeature.OPEN
        self._attr_should_poll = False

    @property
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        if not self.coordinator.data:
            return None

        device_data = self._get_device_data()
        if not device_data:
            return None

        status = device_data.get("status", "UNKNOWN")
        LOGGER.warning("Lock %s status: %s", self.device_id, status)
        
        return status.upper() in ["LOCKED", "SECURED"]

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
            "battery_level": device_data.get("battery", None),
            "signal_strength": device_data.get("signal", None),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
        }

    def _get_device_data(self) -> dict[str, Any] | None:
        """Get the current device data from coordinator."""
        if not self.coordinator.data:
            return None

        locks = self.coordinator.data.get("locks", {})
        return locks.get(self.device_id)

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        LOGGER.warning("Locking %s", self.device_id)
        # TODO: Implement actual lock command to My Verisure API
        await self.coordinator.async_request_refresh()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        LOGGER.warning("Unlocking %s", self.device_id)
        # TODO: Implement actual unlock command to My Verisure API
        await self.coordinator.async_request_refresh()

    async def async_open(self, **kwargs: Any) -> None:
        """Open the lock."""
        LOGGER.warning("Opening %s", self.device_id)
        # TODO: Implement actual open command to My Verisure API
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
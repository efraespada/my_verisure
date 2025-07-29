"""Platform for My Verisure cameras."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.camera import Camera
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
    """Set up My Verisure cameras based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    entities = []

    # Get cameras
    cameras = coordinator.data.get("cameras", {})
    for device_id, device_data in cameras.items():
        entities.append(
            MyVerisureCamera(
                coordinator,
                config_entry,
                device_id,
                device_data,
            )
        )

    async_add_entities(entities)


class MyVerisureCamera(Camera):
    """Representation of a My Verisure camera."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        device_id: str,
        device_data: dict[str, Any],
    ) -> None:
        """Initialize the camera."""
        super().__init__()
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.device_id = device_id
        self.device_data = device_data
        self._attr_name = f"Camera {device_id}"
        self._attr_unique_id = f"{config_entry.entry_id}_{device_id}"
        self._attr_should_poll = False

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
            "recording": device_data.get("recording", False),
            "motion_detected": device_data.get("motion_detected", False),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
        }

    def _get_device_data(self) -> dict[str, Any] | None:
        """Get the current device data from coordinator."""
        if not self.coordinator.data:
            return None

        cameras = self.coordinator.data.get("cameras", {})
        return cameras.get(self.device_id)

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

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        # TODO: Implement actual camera image retrieval from My Verisure API
        LOGGER.warning("Camera image requested for %s", self.device_id)
        return None 
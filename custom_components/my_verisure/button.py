"""Button entities for My Verisure integration."""

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .core.const import DOMAIN
from .coordinator import MyVerisureDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class RefreshCameraImagesButton(CoordinatorEntity, ButtonEntity):
    """Button entity for refreshing camera images."""

    def __init__(self, coordinator, installation_id: str):
        """Initialize the refresh camera images button."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._installation_id = installation_id
        self._attr_name = "Refresh Camera Images"
        self._attr_unique_id = f"verisure_refresh_camera_images_{installation_id}"
        self._attr_device_info = {
            "identifiers": {("verisure", "camera_refresh")},
            "name": "Verisure Camera Refresh",
            "manufacturer": "Verisure",
        }
        # Track if button is currently executing
        self._is_executing = False

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._is_executing:
            _LOGGER.warning("Button is already executing, ignoring press")
            return
            
        _LOGGER.warning("Refreshing camera images...")
        
        # Set executing state
        self._is_executing = True
        self.async_write_ha_state()
        
        try:
            # Use the service to refresh camera images
            await self.hass.services.async_call(
                DOMAIN,
                "refresh_camera_images",
                {"installation_id": self._installation_id}
            )
            _LOGGER.warning("Camera images refresh service called successfully")
                
        except Exception as e:
            _LOGGER.error("Failed to refresh camera images: %s", e)
        finally:
            # Clear executing state
            self._is_executing = False
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Button is available only if coordinator is working and not currently executing
        return self.coordinator.last_update_success and not self._is_executing

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "installation_id": self._installation_id,
            "action": "refresh_camera_images",
            "description": "Refresh images from all Verisure cameras",
            "is_executing": self._is_executing,
        }

    def clear_executing_state(self) -> None:
        """Clear the executing state and update the entity."""
        self._is_executing = False
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        # Register with coordinator for state updates
        self.coordinator.register_button(self)
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verisure button entities."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    
    # Wait for coordinator data to be available
    if not coordinator.data:
        _LOGGER.warning("Coordinator data not available yet")
        return

    buttons = []
    
    # Get installation ID from coordinator data
    installation_id = coordinator.data.get("installation_id")
    if installation_id:
        # Create refresh camera images button
        refresh_button = RefreshCameraImagesButton(coordinator, installation_id)
        buttons.append(refresh_button)
        _LOGGER.info("Created refresh camera images button for installation %s", installation_id)

    if buttons:
        async_add_entities(buttons, update_before_add=True)
        _LOGGER.info("Added %d Verisure button entities", len(buttons))
    else:
        _LOGGER.info("No button entities created")

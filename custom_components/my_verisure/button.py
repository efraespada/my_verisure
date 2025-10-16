"""Button entities for My Verisure integration."""

import logging
from typing import Optional

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .core.const import DOMAIN
from .coordinator import MyVerisureDataUpdateCoordinator
from .core.dependency_injection.providers import (
    setup_dependencies,
    get_refresh_camera_images_use_case,
    clear_dependencies,
)
from .core.session_manager import get_session_manager

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

    async def async_press(self) -> None:
        """Handle the button press."""
        try:
            _LOGGER.warning("🔄 Refreshing camera images for installation %s", self._installation_id)
            
            # Ensure coordinator is logged in and has valid session
            if not await self._coordinator.async_login():
                _LOGGER.error("❌ Failed to login to My Verisure")
                return
            
            # Check SessionManager state
            session_manager = get_session_manager()
            _LOGGER.warning("🔑 SessionManager state - Authenticated: %s, Hash: %s", 
                          session_manager.is_authenticated, 
                          session_manager.get_current_hash_token()[:20] + "..." if session_manager.get_current_hash_token() else "None")
            
            # Setup dependencies before using the use case
            # Note: Coordinator already has dependencies setup, but we need to ensure
            # they are available for the use case
            try:
                setup_dependencies()
                _LOGGER.warning("🔧 Dependencies configured successfully")
            except Exception as dep_error:
                _LOGGER.warning("⚠️ Dependencies already configured or error: %s", dep_error)
            
            try:
                # Get the refresh camera images use case
                refresh_use_case = get_refresh_camera_images_use_case()
                
                # Execute the refresh camera images use case
                result = await refresh_use_case.refresh_camera_images(
                    installation_id=self._installation_id,
                    max_attempts=30,
                    check_interval=4,
                )
                
                _LOGGER.warning(
                    "✅ Camera images refresh completed: %d cameras processed, %d successful, %d failed",
                    result.total_cameras,
                    result.successful_refreshes,
                    result.failed_refreshes
                )
                
                # Update the coordinator data to trigger entity updates
                await self._coordinator.async_request_refresh()
                
            finally:
                # Clean up dependencies
                clear_dependencies()
            
        except Exception as e:
            _LOGGER.error("❌ Failed to refresh camera images: %s", e)
            raise

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "installation_id": self._installation_id,
            "action": "refresh_camera_images",
            "description": "Refresh images from all Verisure cameras",
        }


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

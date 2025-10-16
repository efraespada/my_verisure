"""Camera entities for My Verisure integration."""

import logging
import os
from datetime import datetime
from typing import Optional

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .core.file_manager import get_file_manager
from .core.const import DOMAIN
from .coordinator import MyVerisureDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class VerisureCamera(CoordinatorEntity, Camera):
    """Camera entity for Verisure cameras."""

    def __init__(self, coordinator, device):
        """Initialize the camera entity."""
        super().__init__(coordinator)
        self._device = device
        self._attr_name = f"Verisure {device['name']}"
        self._attr_unique_id = f"verisure_camera_{device['code']}"
        self._attr_device_info = {
            "identifiers": {("verisure", device['code'])},
            "name": device['name'],
            "manufacturer": "Verisure",
            "model": f"{device['type']} Camera",
        }
        self._file_manager = get_file_manager()
        self._latest_image_path = None
        self._latest_image_timestamp = None

    @property
    def camera_image(self) -> Optional[bytes]:
        """Return the latest camera image."""
        return self._get_latest_image()

    def _get_latest_image(self) -> Optional[bytes]:
        """Get the most recent image for this camera."""
        try:
            # Get the camera directory path
            camera_dir = self._file_manager.get_data_path()
            device_path = os.path.join(camera_dir, "cameras", f"{self._device['type']}{self._device['code']:02d}")
            
            if not os.path.exists(device_path):
                _LOGGER.debug("Camera directory not found: %s", device_path)
                return None

            # Find the most recent timestamp directory
            latest_timestamp = None
            latest_timestamp_dir = None
            
            for item in os.listdir(device_path):
                item_path = os.path.join(device_path, item)
                if os.path.isdir(item_path):
                    try:
                        # Parse timestamp from directory name (format: 2025-10-16_06-10-44)
                        timestamp_str = item.replace("_", " ").replace("-", ":")
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            latest_timestamp_dir = item_path
                    except ValueError:
                        _LOGGER.debug("Could not parse timestamp from directory: %s", item)
                        continue

            if latest_timestamp_dir is None:
                _LOGGER.debug("No valid timestamp directories found for camera %s", self._device['code'])
                return None

            # Look for thumbnail.jpg in the latest directory
            thumbnail_path = os.path.join(latest_timestamp_dir, "thumbnail.jpg")
            if os.path.exists(thumbnail_path):
                with open(thumbnail_path, "rb") as f:
                    image_data = f.read()
                    self._latest_image_path = thumbnail_path
                    self._latest_image_timestamp = latest_timestamp.isoformat()
                    _LOGGER.debug("Loaded latest image for camera %s from %s", self._device['code'], thumbnail_path)
                    return image_data
            else:
                _LOGGER.debug("Thumbnail not found in latest directory: %s", latest_timestamp_dir)
                return None

        except Exception as e:
            _LOGGER.error("Error getting latest image for camera %s: %s", self._device['code'], e)
            return None

    @property
    def extra_state_attributes(self):
        """Return additional state attributes."""
        return {
            "device_type": self._device['type'],
            "device_code": self._device['code'],
            "device_name": self._device['name'],
            "latest_image_path": self._latest_image_path,
            "latest_image_timestamp": self._latest_image_timestamp,
            "is_active": self._device.get('is_active'),
            "remote_use": self._device.get('remote_use'),
        }

    async def async_camera_image(self) -> Optional[bytes]:
        """Return the latest camera image asynchronously."""
        return self._get_latest_image()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verisure camera entities."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]
    
    # Wait for coordinator data to be available
    if not coordinator.data:
        _LOGGER.warning("Coordinator data not available yet")
        return

    cameras = []
    
    # Get devices from coordinator data
    devices = coordinator.data.get("devices", [])
    
    # Filter for camera devices (YP and YR)
    camera_devices = [
        device for device in devices 
        if device.get('type') in ["YP", "YR"] and device.get('remote_use')
    ]
    
    for device in camera_devices:
        camera = VerisureCamera(coordinator, device)
        cameras.append(camera)
        _LOGGER.info("Created camera entity for %s (%s)", device['name'], f"{device['type']}{device['code']:02d}")

    if cameras:
        async_add_entities(cameras, update_before_add=True)
        _LOGGER.info("Added %d Verisure camera entities", len(cameras))
    else:
        _LOGGER.info("No camera devices found to create entities")

"""Camera entities for My Verisure integration."""

import logging
import os

from datetime import datetime
from typing import Optional

from homeassistant.components.camera import Camera
from homeassistant.components.camera import CameraEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MyVerisureDataUpdateCoordinator
from .device import get_device_info

_LOGGER = logging.getLogger(__name__)


class VerisureCamera(CoordinatorEntity, Camera):
    """Camera entity for Verisure cameras."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        device: dict,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the camera entity."""
        super().__init__(coordinator)
        self._my_coordinator = coordinator
        self._device = device
        self._attr_name = f"Verisure {device['name']}"
        self._attr_unique_id = f"{config_entry.entry_id}_camera_{device['code']}"
        self._attr_device_info = get_device_info(config_entry)
        self._latest_image_path: str | None = None
        self._latest_image_timestamp: str | None = None
        self._sync_image_cache: bytes | None = None
        
        self._attr_supported_features = CameraEntityFeature(0)
        self.content_type = "image/jpeg"

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> Optional[bytes]:
        """Return the latest cached image (sync API); prefer async_camera_image."""
        return self._sync_image_cache

    def _get_latest_image(self) -> Optional[bytes]:
        """Get the most recent image for this camera."""
        try:
            # Get the camera directory path
            camera_dir = self._my_coordinator.file_manager.get_data_directory()
            device_path = os.path.join(camera_dir, "cameras", f"{self._device['type']}{int(self._device['code']):02d}")
            
            _LOGGER.debug("Looking for camera images in: %s", device_path)
        
            if not os.path.exists(device_path):
                _LOGGER.warning("Camera directory not found: %s", device_path)
                return None

            # List all items in the camera directory
            try:
                items = os.listdir(device_path)
                _LOGGER.debug("Found %d items in camera directory: %s", len(items), items)
            except Exception as e:
                _LOGGER.error("Error listing camera directory %s: %s", device_path, e)
                return None

            # Find the most recent timestamp directory
            latest_timestamp: datetime | None = None
            latest_timestamp_dir: str | None = None
            
            for item in items:
                item_path = os.path.join(device_path, item)
                if os.path.isdir(item_path):
                    try:
                        # Parse timestamp from directory name (format: 2025-01-16_06-10-44)
                        # Convert "2025-01-16_06-10-44" to "2025-01-16 06:10:44"
                        timestamp_str = item.replace("_", " ")
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H-%M-%S")
                        
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            latest_timestamp_dir = item_path
                            _LOGGER.debug("Found newer timestamp directory: %s (parsed as %s)", item, timestamp)
                    except ValueError as e:
                        _LOGGER.debug("Could not parse timestamp from directory '%s': %s", item, e)
                        continue

            if latest_timestamp_dir is None or latest_timestamp is None:
                _LOGGER.warning("No valid timestamp directories found for camera %s in %s", self._device['code'], device_path)
                return None

            _LOGGER.debug("Using latest timestamp directory: %s", latest_timestamp_dir)

            # Look for thumbnail.jpg in the latest directory
            thumbnail_path = os.path.join(latest_timestamp_dir, "thumbnail.jpg")
            if os.path.exists(thumbnail_path):
                with open(thumbnail_path, "rb") as f:
                    image_data = f.read()
                    self._latest_image_path = thumbnail_path
                    self._latest_image_timestamp = latest_timestamp.isoformat()
                    _LOGGER.info("✅ Loaded latest image for camera %s from %s (size: %d bytes)", 
                               self._device['code'], thumbnail_path, len(image_data))
                    return image_data
            else:
                # Try to find any image file in the directory
                try:
                    files = os.listdir(latest_timestamp_dir)
                    _LOGGER.debug("Files in latest directory: %s", files)
                    
                    # Look for any image file
                    for file in files:
                        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                            image_path = os.path.join(latest_timestamp_dir, file)
                            with open(image_path, "rb") as f:
                                image_data = f.read()
                                self._latest_image_path = image_path
                                self._latest_image_timestamp = latest_timestamp.isoformat()
                                _LOGGER.info("✅ Loaded image for camera %s from %s (size: %d bytes)", 
                                           self._device['code'], image_path, len(image_data))
                                return image_data
                except Exception as e:
                    _LOGGER.error("Error reading files from directory %s: %s", latest_timestamp_dir, e)
                
                _LOGGER.warning("No thumbnail.jpg or other images found in latest directory: %s", latest_timestamp_dir)
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

    async def async_camera_image(self, width: Optional[int] = None, height: Optional[int] = None) -> Optional[bytes]:
        """Return the latest camera image asynchronously.

        Width and height are ignored because this camera only serves static images.
        """
        image = await self.hass.async_add_executor_job(self._get_latest_image)
        self._sync_image_cache = image
        return image

    async def stream_source(self) -> str | None:
        """Static-image cameras do not expose a stream."""
        return None

    async def async_refresh_providers(self, *, write_state: bool = True) -> None:
        """Refresh camera providers."""
        # This method is required by Home Assistant Camera component
        # We don't need to implement WebRTC or streaming for static images
        pass


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Verisure camera entities."""
    coordinator: MyVerisureDataUpdateCoordinator = config_entry.runtime_data
    
    # Wait for coordinator data to be available
    if not coordinator.data:
        _LOGGER.warning("Coordinator data not available yet")
        return

    cameras = []
    
    # Get devices from coordinator data
    devices = coordinator.data.get("detailed_installation", {}).get("installation", {}).get("devices", [])
    
    # Filter for camera devices (YP and YR)
    camera_devices = [
        device for device in devices 
        if device.get('type') in ["YP", "YR"]
    ]
    
    for device in camera_devices:
        camera = VerisureCamera(coordinator, device, config_entry)
        cameras.append(camera)
        _LOGGER.info("Created camera entity for %s (%s)", device['name'], f"{device['type']}{int(device['code']):02d}")

    if cameras:
        async_add_entities(cameras, update_before_add=True)
        _LOGGER.info("Added %d Verisure camera entities", len(cameras))
    else:
        _LOGGER.info("No camera devices found to create entities")

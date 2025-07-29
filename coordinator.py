"""DataUpdateCoordinator for the My Verisure integration."""

from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MyVerisureClient
from .api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
)
from .const import CONF_INSTALLATION_ID, CONF_USER, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


class MyVerisureDataUpdateCoordinator(DataUpdateCoordinator):
    """A My Verisure Data Update Coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the My Verisure hub."""
        self.hass = hass
        self.installation_id = entry.data.get(CONF_INSTALLATION_ID)
        
        # Session file path
        session_file = hass.config.path(
            STORAGE_DIR, f"my_verisure_{entry.data[CONF_USER]}.json"
        )
        
        self.client = MyVerisureClient(
            user=entry.data[CONF_USER],
            password=entry.data[CONF_PASSWORD],
        )
        
        # Try to load existing session
        if self.client.load_session(session_file):
            LOGGER.info("Session loaded from storage")
        else:
            LOGGER.info("No existing session found")

        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )

    async def async_login(self) -> bool:
        """Login to My Verisure."""
        try:
            await self.client.connect()
            
            # Check if we have a valid session
            if self.client.is_session_valid():
                LOGGER.info("Using existing valid session")
                return True
            
            # Perform login
            await self.client.login()
            
            # Save session after successful login
            session_file = self.hass.config.path(
                STORAGE_DIR, f"my_verisure_{self.client.user}.json"
            )
            self.client.save_session(session_file)
            
            return True
        except MyVerisureAuthenticationError as ex:
            LOGGER.error("Authentication failed for My Verisure: %s", ex)
            raise ConfigEntryAuthFailed("Authentication failed") from ex
        except MyVerisureError as ex:
            LOGGER.error("Could not log in to My Verisure: %s", ex)
            return False

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from My Verisure."""
        try:
            # Get all devices for the installation
            devices = await self.client.get_devices(self.installation_id or "")
            
            # Organize devices by type
            organized_data = {
                "alarm": self._get_alarm_state(devices),
                "cameras": self._filter_devices_by_type(devices, ["CAMERA", "SMARTCAMERA"]),
                "climate": self._filter_devices_by_type(devices, ["CLIMATE", "HUMIDITY", "TEMPERATURE"]),
                "door_window": self._filter_devices_by_type(devices, ["DOOR", "WINDOW", "PIR"]),
                "locks": self._filter_devices_by_type(devices, ["LOCK", "SMARTLOCK"]),
                "smart_plugs": self._filter_devices_by_type(devices, ["SMARTPLUG", "PLUG"]),
                "sensors": self._filter_devices_by_type(devices, ["SENSOR", "MOTION", "SMOKE", "WATER"]),
            }
            
            return organized_data
            
        except MyVerisureAuthenticationError as ex:
            LOGGER.error("Authentication failed during update: %s", ex)
            raise ConfigEntryAuthFailed("Authentication failed") from ex
        except MyVerisureConnectionError as ex:
            LOGGER.error("Connection error during update: %s", ex)
            raise UpdateFailed("Connection error") from ex
        except MyVerisureError as ex:
            LOGGER.error("Error updating data: %s", ex)
            raise UpdateFailed(f"Update failed: {ex}") from ex

    def _get_alarm_state(self, devices: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract alarm state from devices."""
        # Look for alarm panel or control device
        alarm_devices = self._filter_devices_by_type(devices, ["ALARM", "PANEL", "CONTROL"])
        
        if alarm_devices:
            alarm_device = list(alarm_devices.values())[0]
            return {
                "state": alarm_device.get("status", "UNKNOWN"),
                "device": alarm_device,
            }
        
        return {"state": "UNKNOWN", "device": None}

    def _filter_devices_by_type(
        self, devices: list[Dict[str, Any]], device_types: list[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Filter devices by type and organize by device ID."""
        filtered_devices = {}
        
        for device in devices:
            device_type = device.get("type", "").upper()
            if any(dt in device_type for dt in device_types):
                device_id = device.get("id", device.get("name", "unknown"))
                filtered_devices[device_id] = device
        
        return filtered_devices

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.client:
            await self.client.disconnect() 
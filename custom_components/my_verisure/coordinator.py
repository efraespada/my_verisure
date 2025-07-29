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
    MyVerisureOTPError,
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
        
        # Store session file path for later loading
        self.session_file = session_file

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
                LOGGER.warning("Using existing valid session")
                # Try to use the session by making a test request
                try:
                    # Test the session by trying to get installations
                    LOGGER.warning("Testing session with JWT token: %s", 
                                "Present" if self.client._token else "None")
                    await self.client.get_installations()
                    LOGGER.warning("Session is valid and working")
                    return True
                except MyVerisureOTPError:
                    LOGGER.warning("Session requires OTP re-authentication")
                    # Fall through to re-authentication
                except Exception as e:
                    LOGGER.warning("Session test failed, will re-authenticate: %s", e)
                    # Fall through to re-authentication
            
            # If we don't have a valid session, we cannot proceed automatically
            # because we might need OTP which requires user interaction
            LOGGER.warning("No valid session available and cannot perform automatic login due to potential OTP requirement")
            raise ConfigEntryAuthFailed("otp_reauth_required")
            
        except MyVerisureOTPError as ex:
            LOGGER.error("OTP authentication required but cannot be handled automatically: %s", ex)
            # This is a special case - we need to trigger re-authentication
            raise ConfigEntryAuthFailed("otp_reauth_required") from ex
        except MyVerisureAuthenticationError as ex:
            LOGGER.error("Authentication failed for My Verisure: %s", ex)
            raise ConfigEntryAuthFailed("Authentication failed") from ex
        except MyVerisureError as ex:
            LOGGER.error("Could not log in to My Verisure: %s", ex)
            return False

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from My Verisure."""
        try:
            # Check if we can operate without login
            if not self.can_operate_without_login():
                LOGGER.warning("Cannot operate without valid session - triggering re-authentication")
                raise ConfigEntryAuthFailed("otp_reauth_required")
            
            # Get all devices for the installation
            devices = await self.client.get_devices(self.installation_id or "")
            
            LOGGER.warning("Retrieved %d devices from My Verisure", len(devices))
            
            # Get services for the installation
            services = await self.client.get_installation_services(self.installation_id or "")
            
            LOGGER.warning("Retrieved services from My Verisure: %d services found", 
                          len(services.get("services", [])))
            
            # Log alarm-related services
            alarm_services = []
            for service in services.get("services", []):
                request = service.get("request", "")
                if request in ["DARM", "ARM", "ARMDAY", "ARMNIGHT", "PERI"]:
                    alarm_services.append(f"{request}({service.get('idService', 'N/A')})")
            
            if alarm_services:
                LOGGER.warning("Alarm services available: %s", ", ".join(alarm_services))
            
            # Organize devices by type
            organized_data = {
                "alarm": self._get_alarm_state(devices),
                "cameras": self._filter_devices_by_type(devices, ["CAMERA", "SMARTCAMERA"]),
                "climate": self._filter_devices_by_type(devices, ["CLIMATE", "HUMIDITY", "TEMPERATURE"]),
                "door_window": self._filter_devices_by_type(devices, ["DOOR", "WINDOW", "PIR"]),
                "locks": self._filter_devices_by_type(devices, ["LOCK", "SMARTLOCK"]),
                "smart_plugs": self._filter_devices_by_type(devices, ["SMARTPLUG", "PLUG"]),
                "sensors": self._filter_devices_by_type(devices, ["SENSOR", "MOTION", "SMOKE", "WATER"]),
                "services": services,  # Add services data
            }
            
            LOGGER.warning("Organized data: %s", {k: len(v) for k, v in organized_data.items()})
            
            return organized_data
            
        except MyVerisureOTPError as ex:
            LOGGER.error("OTP authentication required during update: %s", ex)
            raise ConfigEntryAuthFailed("otp_reauth_required") from ex
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

    async def async_load_session(self) -> bool:
        """Load session data asynchronously."""
        if hasattr(self, 'session_file'):
            if await self.client.load_session(self.session_file):
                LOGGER.warning("Session loaded from storage")
                LOGGER.warning("Client JWT token after loading: %s", 
                            "Present" if self.client._token else "None")
                if self.client._token:
                    LOGGER.warning("JWT token length: %d characters", len(self.client._token))
                else:
                    LOGGER.warning("Session loaded but no JWT token found - session may be invalid")
                return True
            else:
                LOGGER.warning("No existing session found")
                return False
        return False

    def can_operate_without_login(self) -> bool:
        """Check if the coordinator can operate without requiring login."""
        return self.client.is_session_valid() and self.client._token is not None

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.client:
            await self.client.disconnect() 
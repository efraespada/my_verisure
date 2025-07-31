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
                                "Present" if self.client._hash else "None")
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
            
            # Ensure client is connected
            LOGGER.warning("Checking client connection status...")
            LOGGER.warning("Client session exists: %s", "Yes" if self.client._session else "No")
            LOGGER.warning("Client GraphQL client exists: %s", "Yes" if self.client._client else "No")
            
            if not self.client._client:
                LOGGER.warning("Client not connected, connecting now...")
                await self.client.connect()
                LOGGER.warning("Client connected successfully")
            
            # First, get services for the installation to know what's available
            LOGGER.warning("Getting services for installation %s", self.installation_id)
            services = await self.client.get_installation_services(self.installation_id or "")
            
            LOGGER.warning("Retrieved services from My Verisure: %d services found", 
                          len(services.get("services", [])))
            
            # Analyze services to determine what devices/functionality are available
            available_features = self._analyze_services(services.get("services", []))
            
            LOGGER.warning("Available features based on services: %s", available_features)
            
            # Get devices only if we have device-related services
            devices = []
            if available_features.get("has_devices", False):
                devices = await self.client.get_devices(self.installation_id or "")
                LOGGER.warning("Retrieved %d devices from My Verisure", len(devices))
            
            # Organize data based on available services
            organized_data = {
                "alarm": self._get_alarm_state_from_services(services, devices),
                "cameras": self._get_cameras_from_services(services, devices),
                "climate": self._get_climate_from_services(services, devices),
                "door_window": self._get_door_window_from_services(services, devices),
                "locks": self._get_locks_from_services(services, devices),
                "smart_plugs": self._get_smart_plugs_from_services(services, devices),
                "sensors": self._get_sensors_from_services(services, devices),
                "services": services,  # Keep full services data
                "available_features": available_features,  # Add feature summary
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

    def _analyze_services(self, services: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze services to determine available features."""
        features = {
            "has_alarm": False,
            "has_cameras": False,
            "has_climate": False,
            "has_door_window": False,
            "has_locks": False,
            "has_smart_plugs": False,
            "has_sensors": False,
            "has_devices": False,
            "alarm_services": [],
            "device_services": [],
        }
        
        for service in services:
            request = service.get("request", "")
            active = service.get("active", False)
            
            if not active:
                continue
                
            # Alarm services
            if request in ["DARM", "ARM", "ARMDAY", "ARMNIGHT", "PERI"]:
                features["has_alarm"] = True
                features["alarm_services"].append({
                    "request": request,
                    "id": service.get("idService", ""),
                    "active": active
                })
            
            # Device-related services
            elif request in ["EST", "ESTINV", "IMG", "CAMA", "CAMERAS"]:
                features["has_devices"] = True
                features["device_services"].append({
                    "request": request,
                    "id": service.get("idService", ""),
                    "active": active
                })
                
                # Specific device types
                if request in ["IMG", "CAMA", "CAMERAS"]:
                    features["has_cameras"] = True
                elif request in ["EST", "ESTINV"]:
                    features["has_sensors"] = True
        
        LOGGER.warning("Service analysis: %s", features)
        return features

    def _get_alarm_state_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract alarm state from services and devices."""
        services_list = services.get("services", [])
        installation = services.get("installation", {})
        
        # Check if we have alarm services
        alarm_services = []
        for service in services_list:
            request = service.get("request", "")
            if request in ["DARM", "ARM", "ARMDAY", "ARMNIGHT", "PERI"] and service.get("active", False):
                alarm_services.append(service)
        
        if not alarm_services:
            return {"state": "UNKNOWN", "device": None, "available_commands": []}
        
        # For now, return basic alarm info
        # TODO: Get actual alarm state from devices or another API call
        return {
            "state": "DARM",  # Default to disarmed
            "device": {
                "id": "alarm_panel",
                "type": "ALARM",
                "installation_id": installation.get("numinst", "Unknown"),
                "panel": installation.get("panel", "Unknown"),
            },
            "available_commands": [s.get("request") for s in alarm_services],
            "services": alarm_services,
        }

    def _get_cameras_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get cameras based on services and devices."""
        # Check if camera services are available
        services_list = services.get("services", [])
        has_camera_service = any(
            s.get("request") in ["IMG", "CAMA", "CAMERAS"] and s.get("active", False)
            for s in services_list
        )
        
        if not has_camera_service:
            return {}
        
        # Filter devices for cameras
        return self._filter_devices_by_type(devices, ["CAMERA", "SMARTCAMERA"])

    def _get_climate_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get climate sensors based on services and devices."""
        # For now, return empty as we don't have specific climate services
        return self._filter_devices_by_type(devices, ["CLIMATE", "HUMIDITY", "TEMPERATURE"])

    def _get_door_window_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get door/window sensors based on services and devices."""
        # Check if device inventory service is available
        services_list = services.get("services", [])
        has_device_service = any(
            s.get("request") in ["EST", "ESTINV"] and s.get("active", False)
            for s in services_list
        )
        
        if not has_device_service:
            return {}
        
        # Filter devices for door/window sensors
        return self._filter_devices_by_type(devices, ["DOOR", "WINDOW", "PIR"])

    def _get_locks_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get locks based on services and devices."""
        # Check if key service is available
        services_list = services.get("services", [])
        has_key_service = any(
            s.get("request") == "KEY" and s.get("active", False)
            for s in services_list
        )
        
        if not has_key_service:
            return {}
        
        # Filter devices for locks
        return self._filter_devices_by_type(devices, ["LOCK", "SMARTLOCK"])

    def _get_smart_plugs_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get smart plugs based on services and devices."""
        # For now, return empty as we don't have specific smart plug services
        return self._filter_devices_by_type(devices, ["SMARTPLUG", "PLUG"])

    def _get_sensors_from_services(self, services: Dict[str, Any], devices: list[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get sensors based on services and devices."""
        # Check if device inventory service is available
        services_list = services.get("services", [])
        has_device_service = any(
            s.get("request") in ["EST", "ESTINV"] and s.get("active", False)
            for s in services_list
        )
        
        if not has_device_service:
            return {}
        
        # Filter devices for sensors
        return self._filter_devices_by_type(devices, ["SENSOR", "MOTION", "SMOKE", "WATER"])

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
                            "Present" if self.client._hash else "None")
                if self.client._hash:
                    LOGGER.warning("JWT token length: %d characters", len(self.client._hash))
                else:
                    LOGGER.warning("Session loaded but no JWT token found - session may be invalid")
                return True
            else:
                LOGGER.warning("No existing session found")
                return False
        return False

    def can_operate_without_login(self) -> bool:
        """Check if the coordinator can operate without requiring login."""
        return self.client.is_session_valid() and self.client._hash is not None

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self.client:
            await self.client.disconnect() 
"""DataUpdateCoordinator for the My Verisure integration."""

from __future__ import annotations

import json
import time
from typing import Any, Dict
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
)
from core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    get_session_use_case,
    get_installation_use_case,
    get_alarm_use_case,
    clear_dependencies,
)
from .const import CONF_INSTALLATION_ID, CONF_USER, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER, CONF_SCAN_INTERVAL


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
        
        # Setup dependencies with credentials
        setup_dependencies(
            username=entry.data[CONF_USER],
            password=entry.data[CONF_PASSWORD],
        )
        
        # Get use cases
        self.auth_use_case = get_auth_use_case()
        self.session_use_case = get_session_use_case()
        self.installation_use_case = get_installation_use_case()
        self.alarm_use_case = get_alarm_use_case()
        
        # Store session file path for later loading
        self.session_file = session_file

        # Get scan interval from config entry
        scan_interval_minutes = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        # Ensure it's an integer
        try:
            scan_interval_minutes = int(scan_interval_minutes)
        except (ValueError, TypeError):
            LOGGER.warning("Invalid scan_interval value: %s, using default: %s", scan_interval_minutes, DEFAULT_SCAN_INTERVAL)
            scan_interval_minutes = DEFAULT_SCAN_INTERVAL
        
        LOGGER.warning("Coordinator: Using scan_interval=%s minutes (from config: %s, default: %s)", 
                      scan_interval_minutes, entry.data.get(CONF_SCAN_INTERVAL), DEFAULT_SCAN_INTERVAL)
        scan_interval = timedelta(minutes=scan_interval_minutes)

        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def async_login(self) -> bool:
        """Login to My Verisure."""
        try:
            # Check if we have a valid session
            if self.session_use_case.is_session_valid():
                LOGGER.warning("Using existing valid session")
                # Try to use the session by making a test request
                try:
                    # Test the session by trying to get installations
                    await self.installation_use_case.get_installations()
                    LOGGER.warning("Session is valid and working")
                    return True
                except MyVerisureOTPError:
                    LOGGER.warning("Session requires OTP re-authentication")
                    # Fall through to re-authentication
                except Exception as e:
                    LOGGER.warning("Session test failed, will re-authenticate: %s", e)
                    # Fall through to re-authentication
            
            # If we don't have a valid session, try to refresh it automatically
            LOGGER.warning("No valid session available, attempting automatic refresh...")
            if await self.async_refresh_session():
                return True
            
            # If automatic refresh fails, perform a new login
            LOGGER.warning("Automatic session refresh failed, performing new login...")
            return await self._perform_new_login()
            
        except Exception as e:
            LOGGER.error("Login failed: %s", e)
            return False

    async def async_refresh_session(self) -> bool:
        """Try to refresh the session using saved session data."""
        try:
            # Try to load and validate session
            if await self.session_use_case.load_session(self.session_file):
                if self.session_use_case.is_session_valid():
                    LOGGER.warning("Session refreshed successfully")
                    return True
                else:
                    LOGGER.warning("Loaded session is not valid")
                    return False
            else:
                LOGGER.warning("No session file found or failed to load")
                return False
                
        except Exception as e:
            LOGGER.error("Session refresh failed: %s", e)
            return False

    async def _perform_new_login(self) -> bool:
        """Perform a new login."""
        try:
            # Get credentials from config entry
            username = self.config_entry.data[CONF_USER]
            password = self.config_entry.data[CONF_PASSWORD]
            
            # Perform login using auth use case
            auth_result = await self.auth_use_case.login(username, password)
            
            if auth_result.success:
                # Save session after successful login
                await self.session_use_case.save_session(self.session_file)
                LOGGER.warning("New login successful and session saved")
                return True
            else:
                LOGGER.error("Login failed: %s", auth_result.error_message)
                return False
                
        except MyVerisureOTPError:
            LOGGER.warning("OTP authentication required")
            # This should be handled by the config flow
            raise
        except Exception as e:
            LOGGER.error("New login failed: %s", e)
            return False

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via My Verisure API."""
        try:
            # Ensure we're logged in
            if not await self.async_login():
                raise UpdateFailed("Failed to login to My Verisure")

            # Get alarm status using alarm use case
            alarm_status = await self.alarm_use_case.get_alarm_status(self.installation_id)
            
            # Convert to dictionary format expected by Home Assistant
            return {
                "alarm_status": alarm_status.to_dict() if hasattr(alarm_status, 'to_dict') else alarm_status,
                "last_update": time.time(),
            }
            
        except MyVerisureAuthenticationError as ex:
            LOGGER.error("Authentication error: %s", ex)
            raise ConfigEntryAuthFailed from ex
        except MyVerisureConnectionError as ex:
            LOGGER.error("Connection error: %s", ex)
            raise UpdateFailed(f"Connection error: {ex}") from ex
        except MyVerisureError as ex:
            LOGGER.error("My Verisure error: %s", ex)
            raise UpdateFailed(f"My Verisure error: {ex}") from ex
        except Exception as ex:
            LOGGER.error("Unexpected error: %s", ex)
            raise UpdateFailed(f"Unexpected error: {ex}") from ex

    async def async_arm_away(self) -> bool:
        """Arm the alarm in away mode."""
        try:
            return await self.alarm_use_case.arm_away(self.installation_id)
        except Exception as e:
            LOGGER.error("Failed to arm away: %s", e)
            return False

    async def async_arm_home(self) -> bool:
        """Arm the alarm in home mode."""
        try:
            return await self.alarm_use_case.arm_home(self.installation_id)
        except Exception as e:
            LOGGER.error("Failed to arm home: %s", e)
            return False

    async def async_arm_night(self) -> bool:
        """Arm the alarm in night mode."""
        try:
            return await self.alarm_use_case.arm_night(self.installation_id)
        except Exception as e:
            LOGGER.error("Failed to arm night: %s", e)
            return False

    async def async_disarm(self) -> bool:
        """Disarm the alarm."""
        try:
            return await self.alarm_use_case.disarm(self.installation_id)
        except Exception as e:
            LOGGER.error("Failed to disarm: %s", e)
            return False

    async def async_get_installations(self):
        """Get user installations."""
        try:
            return await self.installation_use_case.get_installations()
        except Exception as e:
            LOGGER.error("Failed to get installations: %s", e)
            return []

    async def async_get_installation_services(self, force_refresh: bool = False):
        """Get installation services."""
        try:
            return await self.installation_use_case.get_installation_services(
                self.installation_id, force_refresh
            )
        except Exception as e:
            LOGGER.error("Failed to get installation services: %s", e)
            return None



    async def async_cleanup(self):
        """Clean up resources."""
        try:
            # Clear dependencies
            clear_dependencies()
            LOGGER.info("Coordinator cleanup completed")
        except Exception as e:
            LOGGER.error("Error during cleanup: %s", e) 
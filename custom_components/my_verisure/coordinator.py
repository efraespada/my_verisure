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

from core.api.client import MyVerisureClient
from core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
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
        
        self.client = MyVerisureClient(
            user=entry.data[CONF_USER],
            password=entry.data[CONF_PASSWORD],
        )
        
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
            
            # If we don't have a valid session, try to refresh it automatically
            LOGGER.warning("No valid session available, attempting automatic refresh...")
            if await self.async_refresh_session():
                LOGGER.warning("Session refreshed successfully during login")
                return True
            else:
                LOGGER.warning("Automatic session refresh failed - may require OTP")
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

    async def async_refresh_session(self) -> bool:
        """Attempt to refresh the session using stored credentials."""
        try:
            LOGGER.warning("Attempting to refresh session with stored credentials...")
            
            # Try to connect and authenticate with stored credentials
            await self.client.connect()
            
            # Perform login to get new session tokens
            LOGGER.warning("Performing login to refresh session...")
            login_success = await self.client.login()
            
            if login_success and self.client.is_session_valid():
                LOGGER.warning("Session refreshed successfully")
                # Save the new session
                if hasattr(self, 'session_file'):
                    await self.client.save_session(self.session_file)
                    LOGGER.warning("New session saved to storage")
                return True
            else:
                LOGGER.warning("Session refresh failed - login unsuccessful or session not valid")
                return False
                
        except MyVerisureOTPError as ex:
            LOGGER.error("OTP required during session refresh: %s", ex)
            # Cannot refresh automatically if OTP is required
            return False
        except MyVerisureAuthenticationError as ex:
            LOGGER.error("Authentication failed during session refresh: %s", ex)
            return False
        except MyVerisureError as ex:
            LOGGER.error("Error during session refresh: %s", ex)
            return False

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from My Verisure."""
        try:
            # Check if we can operate without login
            if not self.can_operate_without_login():
                LOGGER.warning("Session not valid, attempting to refresh...")
                
                # Try to refresh the session automatically
                if await self.async_refresh_session():
                    LOGGER.warning("Session refreshed successfully, proceeding with data update")
                else:
                    LOGGER.warning("Session refresh failed - triggering re-authentication")
                    raise ConfigEntryAuthFailed("otp_reauth_required")
            
            # Ensure client is connected
            LOGGER.warning("Checking client connection status...")
            LOGGER.warning("Client session exists: %s", "Yes" if self.client._session else "No")
            LOGGER.warning("Client GraphQL client exists: %s", "Yes" if self.client._client else "No")
            
            if not self.client._client:
                LOGGER.warning("Client not connected, connecting now...")
                await self.client.connect()
                LOGGER.warning("Client connected successfully")
            
            # Get installation services
            LOGGER.warning("Getting installation services for installation %s", self.installation_id)
            services_data = await self.client.get_installation_services(self.installation_id or "")

            # Get alarm status from services
            LOGGER.warning("Getting alarm status for installation %s", self.installation_id)
            alarm_status = await self.client.get_alarm_status(self.installation_id or "", services_data.get("capabilities", ""))
                        
            # Print the complete JSON response
            LOGGER.warning("=== COMPLETE ALARM STATUS JSON ===")
            LOGGER.warning(json.dumps(alarm_status, indent=2, default=str))
            LOGGER.warning("==================================")
            
            # Return the alarm status data
            return {
                "alarm_status": alarm_status,
                "last_updated": int(time.time())
            }
            
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
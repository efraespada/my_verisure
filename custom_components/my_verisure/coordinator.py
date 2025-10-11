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

from .core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
)
from .core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    get_installation_use_case,
    get_alarm_use_case,
    clear_dependencies,
)
from .core.session_manager import get_session_manager
from .core.const import CONF_INSTALLATION_ID, CONF_USER, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER, CONF_SCAN_INTERVAL


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
        
        # Setup dependencies (no credentials needed, clients will get them from SessionManager)
        setup_dependencies()
        
        # Get use cases
        self.auth_use_case = get_auth_use_case()
        self.installation_use_case = get_installation_use_case()
        self.alarm_use_case = get_alarm_use_case()
        
        # Get session manager
        self.session_manager = get_session_manager()
        
        # Set credentials in session manager
        self.session_manager.update_credentials(
            entry.data[CONF_USER],
            entry.data[CONF_PASSWORD],
            "",  # hash_token will be set after login
            ""   # refresh_token will be set after login
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
            # Check if we have a valid session
            if self.session_manager.is_authenticated:
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
            if await self.session_manager.ensure_authenticated(interactive=False):
                if self.session_manager.is_authenticated:
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
                # Update session manager with new credentials
                self.session_manager.update_credentials(
                    self.session_manager.username,
                    self.session_manager.password,
                    auth_result.hash,
                    auth_result.refresh_token
                )
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
        LOGGER.warning("_async_update_data called (coordinator id=%s)", id(self))
        try:
            # Ensure we're logged in
            if not await self.async_login():
                raise UpdateFailed("Failed to login to My Verisure")

            # Get alarm status using alarm use case
            LOGGER.warning("Attempting to get alarm status for installation: %s", self.installation_id)
            alarm_status = await self.alarm_use_case.get_alarm_status(self.installation_id)
            LOGGER.warning("Alarm status retrieved successfully: %s", type(alarm_status))
            
            # Get installation services
            LOGGER.warning("Getting installation services for: %s", self.installation_id)
            services_data = await self.installation_use_case.get_installation_services(self.installation_id)
            LOGGER.warning("Installation services retrieved: %s", type(services_data))
            
            # Convert to dictionary format expected by Home Assistant
            if hasattr(alarm_status, 'dict'):
                alarm_dict = alarm_status.dict()
                LOGGER.warning("Alarm status converted to dict: %s", alarm_dict)
            else:
                alarm_dict = alarm_status
                LOGGER.warning("Alarm status used as-is (no dict method): %s", alarm_dict)
            
            result = {
                "alarm_status": alarm_dict,
                "services": services_data,
                "last_update": time.time(),
            }
            LOGGER.warning("Coordinator returning data: %s", result)
            LOGGER.warning("Coordinator data type: %s", type(result))
            LOGGER.warning("Coordinator data keys: %s", result.keys())
            # Ensure data is set on the coordinator
            try:
                self.async_set_updated_data(result)
                LOGGER.warning("Coordinator data explicitly set (id=%s)", id(self))
                LOGGER.warning("Coordinator data after set: %s", self.data)
                LOGGER.warning("Coordinator data after set keys: %s", list(self.data.keys()) if isinstance(self.data, dict) else self.data)
            except Exception as set_err:
                LOGGER.error("Failed to set coordinator data explicitly: %s", set_err)
            return result
            
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



    def has_valid_session(self) -> bool:
        """Check if we have a valid session."""
        try:
            return self.session_manager.is_authenticated
        except Exception:
            return False

    def get_session_hash(self) -> str | None:
        """Get the current session hash token."""
        try:
            return self.session_manager.get_current_hash_token()
        except Exception:
            return None

    def can_operate_without_login(self) -> bool:
        """Check if the coordinator can operate without requiring login."""
        return self.has_valid_session()

    async def async_load_session(self) -> bool:
        """Load session data asynchronously."""
        try:
            # SessionManager automatically loads session on initialization
            # Just check if we have valid credentials
            return self.session_manager.is_authenticated
        except Exception as e:
            LOGGER.error("Error loading session: %s", e)
            return False

    async def async_config_entry_first_refresh(self) -> None:
        """Perform the first refresh of the coordinator."""
        try:
            await self.async_request_refresh()
        except Exception as e:
            LOGGER.error("Error during first refresh: %s", e)

    async def async_request_refresh(self) -> None:
        """Request a refresh of the coordinator data."""
        try:
            await self._async_update_data()
        except Exception as e:
            LOGGER.error("Error during refresh: %s", e)

    async def async_cleanup(self):
        """Clean up resources."""
        try:
            # Clear dependencies
            clear_dependencies()
            LOGGER.warning("Coordinator cleanup completed")
        except Exception as e:
            LOGGER.error("Error during cleanup: %s", e) 
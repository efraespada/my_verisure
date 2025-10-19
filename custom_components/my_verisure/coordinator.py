"""DataUpdateCoordinator for the My Verisure integration."""

from __future__ import annotations

import time
from typing import Any, Dict
from datetime import timedelta
import json
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.persistent_notification import async_create

from .core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
    MyVerisureServiceBlockedError,
)
from .core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    get_installation_use_case,
    get_alarm_use_case,
    get_get_installation_devices_use_case,
    clear_dependencies,
    get_refresh_camera_images_use_case,
)
from .core.file_manager import get_file_manager
from .core.session_manager import get_session_manager
from .core.const import CONF_INSTALLATION_ID, CONF_USER, DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER, CONF_SCAN_INTERVAL, COORDINATOR_DATA_FILE, CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL
from .core.api.models.domain.alarm import ArmResult, DisarmResult


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
        self.get_installation_devices_use_case = get_get_installation_devices_use_case()
        self.alarm_use_case = get_alarm_use_case()
        self.refresh_camera_images_use_case = get_refresh_camera_images_use_case()
        
        # Get session manager
        self.session_manager = get_session_manager()
        
        # Get file manager for data persistence
        self.file_manager = get_file_manager()
        
        # Reference to alarm control panel for state updates
        self._alarm_control_panel = None
        
        # Set credentials in session manager
        self.session_manager.update_credentials(
            entry.data[CONF_USER],
            entry.data[CONF_PASSWORD],
            "",  # hash_token will be set after login
            ""   # refresh_token will be set after login
        )
        
        # Store session file path for later loading
        self.session_file = session_file

        # Get scan interval from config entry (options override data)
        scan_interval_minutes = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
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
            
        except MyVerisureServiceBlockedError as ex:
            LOGGER.error("Service temporarily blocked during login: %s", ex)
            # Send service blocked notification
            title = await self.get_translation("notifications.service.blocked.title")
            message = await self.get_translation("notifications.service.blocked.message")
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_service_blocked"
            )
            return False
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
                
        except MyVerisureServiceBlockedError as ex:
            LOGGER.error("Service temporarily blocked during new login: %s", ex)
            # Send service blocked notification
            title = await self.get_translation("notifications.service.blocked.title")
            message = await self.get_translation("notifications.service.blocked.message")
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_service_blocked"
            )
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

            LOGGER.warning("Updating data for installation %s", self.installation_id)
            alarm_status = await self.alarm_use_case.get_alarm_status(self.installation_id)
            LOGGER.warning("Alarm status: %s", alarm_status.dict())
            detailed_installation = await self.installation_use_case.get_installation_services(self.installation_id)
            LOGGER.warning("Detailed installation: %s", detailed_installation.dict())
            
            result = {
                "last_updated": time.time(),
                "installation_id": self.installation_id,
                "alarm_status": alarm_status.dict(),
                "detailed_installation": detailed_installation.dict(),
            }

            try:
                self.async_set_updated_data(result)
                try:
                    save_success = self.file_manager.save_json(COORDINATOR_DATA_FILE, result)
                    if not save_success:
                        LOGGER.error("Failed to save coordinator data to %s", COORDINATOR_DATA_FILE)
                except Exception as save_err:
                    LOGGER.error("Error saving coordinator data to %s: %s", COORDINATOR_DATA_FILE, save_err)
                    
            except Exception as set_err:
                LOGGER.error("Failed to set coordinator data explicitly: %s", set_err)
            return result
            
        except MyVerisureServiceBlockedError as ex:
            LOGGER.error("Service temporarily blocked: %s", ex)
            # Send service blocked notification
            title = await self.get_translation("notifications.service.blocked.title")
            message = await self.get_translation("notifications.service.blocked.message")
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_service_blocked"
            )
            raise UpdateFailed(f"Service temporarily blocked: {ex}") from ex
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

    def load_alarm_info(self) -> Dict[str, Any]:
        """Load the last saved data from coordinator data file."""
        try:
            alarm_info = self.file_manager.load_json(COORDINATOR_DATA_FILE)
            if alarm_info:
                return alarm_info
            else:
                LOGGER.warning("No last data found in %s", COORDINATOR_DATA_FILE)
                return {}
        except Exception as e:
            LOGGER.error("Failed to load last data from %s: %s", COORDINATOR_DATA_FILE, e)
            return {}

    def get_alarm_info_info(self) -> Dict[str, Any]:
        """Get information about the last saved data file."""
        try:
            file_path = self.file_manager.get_file_path(COORDINATOR_DATA_FILE)
            file_size = self.file_manager.get_file_size(COORDINATOR_DATA_FILE)
            exists = self.file_manager.file_exists(COORDINATOR_DATA_FILE)
            
            return {
                "file_path": str(file_path),
                "exists": exists,
                "file_size": file_size,
                "last_modified": file_path.stat().st_mtime if exists else None
            }
        except Exception as e:
            LOGGER.error("Failed to get last data info: %s", e)
            return {"error": str(e)}

    async def async_arm_away(self) -> ArmResult:
        """Arm the alarm in away mode."""
        try:
            auto_arm_perimeter_with_internal = self.config_entry.options.get(
                CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
                self.config_entry.data.get(CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL, False)
            )
            result = await self.alarm_use_case.arm_away(self.installation_id, auto_arm_perimeter_with_internal)
            
            # Check if operation was successful and send notification
            if result.success:
                await self._async_update_data()
                title = await self.get_translation("notifications.title.success")
                message = await self.get_translation("notifications.alarm.arm_away.success")
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_arm_away_success"
                )
            else:
                title = await self.get_translation("notifications.title.error")
                message = await self.get_translation("notifications.alarm.arm_away.error", message=result.message)
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_arm_away_error"
                )
            
            return result
        except Exception as e:
            LOGGER.error("Failed to arm away: %s", e)
            # Send error notification
            title = await self.get_translation("notifications.title.error")
            message = await self.get_translation("notifications.alarm.arm_away.exception", error=str(e))
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_alarm_arm_away_exception"
            )
            return ArmResult(success=False, message=f"Failed to arm away: {e}")

    async def async_arm_home(self) -> ArmResult:
        """Arm the alarm in home mode."""
        try:
            result = await self.alarm_use_case.arm_home(self.installation_id)
            
            # Check if operation was successful and send notification
            if result.success:
                await self._async_update_data()
                title = await self.get_translation("notifications.title.success")
                message = await self.get_translation("notifications.alarm.arm_home.success")
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_arm_home_success"
                )
            else:
                title = await self.get_translation("notifications.title.error")
                message = await self.get_translation("notifications.alarm.arm_home.error", message=result.message)
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_arm_home_error"
                )
            
            return result
        except Exception as e:
            LOGGER.error("Failed to arm home: %s", e)
            # Send error notification
            title = await self.get_translation("notifications.title.error")
            message = await self.get_translation("notifications.alarm.arm_home.exception", error=str(e))
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_alarm_arm_home_exception"
            )
            return ArmResult(success=False, message=f"Failed to arm home: {e}")

    async def async_arm_night(self) -> ArmResult:
        """Arm the alarm in night mode."""
        try:
            auto_arm_perimeter_with_internal = self.config_entry.options.get(
                CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
                self.config_entry.data.get(CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL, False)
            )
            result = await self.alarm_use_case.arm_night(self.installation_id, auto_arm_perimeter_with_internal)
            
            # Check if operation was successful and send notification
            if result.success:
                await self._async_update_data()
                title = await self.get_translation("notifications.title.success")
                message = await self.get_translation("notifications.alarm.arm_night.success")
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_arm_night_success"
                )
            else:
                title = await self.get_translation("notifications.title.error")
                message = await self.get_translation("notifications.alarm.arm_night.error", message=result.message)
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_arm_night_error"
                )
            
            return result
        except Exception as e:
            LOGGER.error("Failed to arm night: %s", e)
            # Send error notification
            title = await self.get_translation("notifications.title.error")
            message = await self.get_translation("notifications.alarm.arm_night.exception", error=str(e))
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_alarm_arm_night_exception"
            )
            return ArmResult(success=False, message=f"Failed to arm night: {e}")

    async def async_disarm(self) -> DisarmResult:
        """Disarm the alarm."""
        try:
            result = await self.alarm_use_case.disarm(self.installation_id)
            
            # Check if operation was successful and send notification
            if result.success:
                await self._async_update_data()
                title = await self.get_translation("notifications.title.success")
                message = await self.get_translation("notifications.alarm.disarm.success")
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_disarm_success"
                )
            else:
                title = await self.get_translation("notifications.title.error")
                message = await self.get_translation("notifications.alarm.disarm.error", message=result.message)
                async_create(
                    self.hass,
                    message,
                    title=title,
                    notification_id="verisure_alarm_disarm_error"
                )
            
            return result
        except Exception as e:
            LOGGER.error("Failed to disarm: %s", e)
            # Send error notification
            title = await self.get_translation("notifications.title.error")
            message = await self.get_translation("notifications.alarm.disarm.exception", error=str(e))
            async_create(
                self.hass,
                message,
                title=title,
                notification_id="verisure_alarm_disarm_exception"
            )
            return DisarmResult(success=False, message=f"Failed to disarm: {e}")

    async def async_refresh_camera_images(self) -> None:
        """Refresh camera images."""
        try:
            LOGGER.warning("Refreshing camera images for installation %s", self.installation_id)
            result = await self.refresh_camera_images_use_case.refresh_camera_images(
                installation_id=self.installation_id,
                max_attempts=30,
                check_interval=4,
            )
            
            LOGGER.warning(
                "✅ Camera images refresh completed: %d cameras processed, %d successful, %d failed",
                result.total_cameras,
                result.successful_refreshes,
                result.failed_refreshes
            )
        except Exception as e:
            LOGGER.error("Failed to refresh camera images: %s", e)

    async def get_translation(self, key: str, **kwargs) -> str:
        """Get translation for a given key (async and non-blocking)."""
        lang = self.hass.config.language or "en"
        translations_dir = Path(__file__).parent / "translations"
        lang_file = translations_dir / f"{lang}.json"
        fallback_file = translations_dir / "en.json"

        # Leer archivos sin bloquear el event loop
        async def _load_json(file_path: Path) -> dict:
            if not file_path.exists():
                return {}
            try:
                # Usamos run_in_executor para evitar bloqueo del hilo principal
                import asyncio
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, file_path.read_text, "utf-8")
            except Exception:
                return "{}"

        try:
            content = await _load_json(lang_file)
            data = json.loads(content)
        except Exception:
            try:
                content = await _load_json(fallback_file)
                data = json.loads(content)
            except Exception:
                data = {}

        # Navegar en el dict usando "puntos" (ej. notifications.alarm.disarm.success)
        value = data
        for part in key.split("."):
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(part)

        if value is None:
            # Si no hay traducción, devolvemos la clave literal
            return key

        # Formatear con kwargs opcionales
        try:
            return value.format(**kwargs)
        except Exception:
            return value

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

    def register_alarm_control_panel(self, alarm_panel) -> None:
        """Register the alarm control panel for state updates."""
        self._alarm_control_panel = alarm_panel
        LOGGER.warning("Alarm control panel registered with coordinator")

    def clear_alarm_transition_state(self) -> None:
        """Clear the transition state of the registered alarm control panel."""
        if self._alarm_control_panel and hasattr(self._alarm_control_panel, 'clear_transition_state'):
            self._alarm_control_panel.clear_transition_state()
            LOGGER.warning("Cleared alarm control panel transition state")

    def register_button(self, button) -> None:
        """Register the button for state updates."""
        self._button = button
        LOGGER.warning("Button registered with coordinator")

    def clear_button_executing_state(self) -> None:
        """Clear the executing state of the registered button."""
        if self._button and hasattr(self._button, 'clear_executing_state'):
            self._button.clear_executing_state()
            LOGGER.warning("Cleared button executing state")

    async def async_cleanup(self):
        """Clean up resources."""
        try:
            # Clear dependencies
            clear_dependencies()
            LOGGER.warning("Coordinator cleanup completed")
        except Exception as e:
            LOGGER.error("Error during cleanup: %s", e) 
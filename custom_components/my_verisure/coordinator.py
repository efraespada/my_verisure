"""DataUpdateCoordinator for the My Verisure integration."""

from __future__ import annotations

import time
from typing import Any, Dict, cast
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.components.persistent_notification import async_create

from .core.api.exceptions import MyVerisureServiceBlockedError
from .core.dependency_injection.composition_root import (
    CompositionRoot,
    build_my_verisure_composition_root,
)
from .core.application.coordinator_authentication import CoordinatorAuthenticationPolicy
from .core.application.coordinator_alarm_commands import COMMANDS
from .core.application.translation_service import TranslationService
from .core.application.coordinator_failure import (
    CoordinatorFailureClassifier,
    CoordinatorFailureKind,
)
from .core.application.coordinator_snapshot import merge_alarm_snapshot
from .core.application.coordinator_snapshot_store import CoordinatorSnapshotStore
from .core.application.coordinator_refresh_effects import CoordinatorRefreshEffects
from .core.application.installation_snapshot_service import InstallationSnapshotService
from .core.use_cases.interfaces.auth_use_case import AuthUseCase
from .core.use_cases.interfaces.installation_use_case import InstallationUseCase
from .core.use_cases.interfaces.alarm_use_case import AlarmUseCase
from .core.use_cases.interfaces.get_installation_devices_use_case import GetInstallationDevicesUseCase
from .core.use_cases.interfaces.refresh_camera_images_use_case import RefreshCameraImagesUseCase
from .core.use_cases.interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase
from .core.session_manager import SessionManager
from .core.file_manager import FileManager
from .core.const import (
    CONF_INSTALLATION_ID,
    CONF_USER,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    LOGGER,
    CONF_SCAN_INTERVAL,
    CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
    CONF_DEV_MODE,
)
from .core.log_utils import redact_sensitive_data, reset_dev_mode, set_dev_mode, should_log_detailed
from .core.api.models.domain.alarm import ArmResult, DisarmResult


class MyVerisureDataUpdateCoordinator(DataUpdateCoordinator):
    """A My Verisure Data Update Coordinator."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        composition_root: CompositionRoot | None = None,
    ) -> None:
        """Initialize the My Verisure hub."""
        self.hass = hass
        self.config_entry = entry
        self.installation_id = entry.data.get(CONF_INSTALLATION_ID)
        
        session_file = hass.config.path(
            STORAGE_DIR, f"my_verisure_{entry.data[CONF_USER]}.json"
        )

        self.composition_root = composition_root or build_my_verisure_composition_root(
            session_file=session_file,
            project_root=Path(hass.config.path(STORAGE_DIR))
            / f"my_verisure_{entry.entry_id}",
        )

        self.auth_use_case = self.composition_root.get(cast(type[Any], AuthUseCase))
        self.installation_use_case = self.composition_root.get(cast(type[Any], InstallationUseCase))
        self.get_installation_devices_use_case = self.composition_root.get(
            cast(type[Any], GetInstallationDevicesUseCase)
        )
        self.alarm_use_case = self.composition_root.get(cast(type[Any], AlarmUseCase))
        self.snapshot_service = InstallationSnapshotService(
            self.installation_use_case,
            self.alarm_use_case,
        )
        self.refresh_camera_images_use_case = self.composition_root.get(
            cast(type[Any], RefreshCameraImagesUseCase)
        )
        self.create_dummy_camera_images_use_case = self.composition_root.get(
            cast(type[Any], CreateDummyCameraImagesUseCase)
        )

        self.session_manager = self.composition_root.get(SessionManager)
        self.file_manager = self.composition_root.get(FileManager)
        self.snapshot_store = CoordinatorSnapshotStore(self.file_manager)
        self.refresh_effects = CoordinatorRefreshEffects(
            self.snapshot_store,
            self.async_set_updated_data,
            self.create_dummy_camera_images_use_case,
        )
        self.authentication_policy = CoordinatorAuthenticationPolicy(
            login=self.async_login,
            load_cache=self.load_alarm_info,
        )
        
        # Reference to alarm control panel for state updates
        self._alarm_control_panel = None
        self._failure_classifier = CoordinatorFailureClassifier()
        self._translation_service = TranslationService(Path(__file__).parent / "translations")
        
        # Set credentials in session manager (memory only; persist after login)
        self.session_manager.update_credentials(
            entry.data[CONF_USER],
            entry.data[CONF_PASSWORD],
            "",
            "",
            persist=False,
        )
        
        # Store session file path for later loading
        self.session_file = session_file

        self._dev_mode = bool(
            entry.options.get(CONF_DEV_MODE, entry.data.get(CONF_DEV_MODE, False))
        )

        # Get scan interval from config entry (options override data)
        scan_interval_minutes = entry.options.get(CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        # Ensure it's an integer
        try:
            scan_interval_minutes = int(scan_interval_minutes)
        except (ValueError, TypeError):
            LOGGER.warning("Invalid scan_interval value: %s, using default: %s", scan_interval_minutes, DEFAULT_SCAN_INTERVAL)
            scan_interval_minutes = DEFAULT_SCAN_INTERVAL
        
        LOGGER.info(
            "My Verisure coordinator: scan_interval=%s min (config default %s min)",
            scan_interval_minutes,
            DEFAULT_SCAN_INTERVAL,
        )
        scan_interval = timedelta(minutes=scan_interval_minutes)

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def async_login(self) -> bool:
        """Login to My Verisure with improved error handling and caching."""
        try:
            LOGGER.debug(
                "AUTH_FLOW[async_login]: authenticated=%s, valid=%s, blocked=%s, has_cache=%s",
                self.session_manager.is_authenticated,
                self.session_manager.is_session_valid(),
                self.session_manager.is_service_blocked(),
                bool(self.load_alarm_info()),
            )
            if self.session_manager.is_service_blocked():
                LOGGER.warning(
                    "Login skipped: service temporarily blocked (cooldown active) - "
                    "will use cached data if available"
                )
                return False

            if self.session_manager.is_authenticated and self.session_manager.is_session_valid():
                LOGGER.debug("Using existing valid session")
                return True

            if not self.session_manager.can_attempt_refresh():
                LOGGER.warning(
                    "Cannot attempt session refresh (authenticated=%s, blocked=%s, valid=%s)",
                    self.session_manager.is_authenticated,
                    self.session_manager.is_service_blocked(),
                    self.session_manager.is_session_valid(),
                )
                return False

            LOGGER.info("Session invalid, attempting automatic refresh...")
            return await self.async_refresh_session()

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
                if self.session_manager.is_session_valid():
                    LOGGER.info("Session refreshed successfully")
                    return True
                LOGGER.warning("Loaded session is not valid")
                return False
            else:
                LOGGER.info("No session file found or failed to load")
                return False
                
        except Exception as e:
            LOGGER.error("Session refresh failed: %s", e)
            return False

    def _panel_capabilities_from_stored_data(
        self,
    ) -> tuple[str | None, str | None]:
        """Extract panel and capabilities from last coordinator payload if present."""
        payload = self.data or {}
        detailed = payload.get("detailed_installation")
        if not detailed or not isinstance(detailed, dict):
            return None, None
        inst = detailed.get("installation")
        if not isinstance(inst, dict):
            return None, None
        panel = inst.get("panel") or None
        caps = inst.get("capabilities") or None
        return panel, caps

    async def _async_refresh_alarm_only(self) -> Dict[str, Any]:
        """Refresh alarm status and merge into existing coordinator data."""
        tok = set_dev_mode(self._dev_mode)
        try:
            if not await self.async_login():
                raise UpdateFailed("Failed to login to My Verisure")

            panel, caps = self._panel_capabilities_from_stored_data()
            if not panel or not caps:
                return await self._async_update_data()

            LOGGER.info(
                "Refreshing alarm state for installation %s", self.installation_id
            )
            alarm_status = await self.alarm_use_case.get_alarm_status(
                self.installation_id,
                panel=panel,
                capabilities=caps,
            )
            detailed_installation = (self.data or {}).get("detailed_installation")
            if not detailed_installation:
                return await self._async_update_data()

            result = merge_alarm_snapshot(
                installation_id=self.installation_id,
                alarm_status=alarm_status.dict(),
                detailed_installation=detailed_installation,
                timestamp=time.time(),
            )
            await self.refresh_effects.apply(
                result,
                self.installation_id,
                create_dummy_images=False,
            )
            LOGGER.info("Alarm state refreshed for installation %s", self.installation_id)
            return result
        finally:
            reset_dev_mode(tok)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via My Verisure API."""
        tok = set_dev_mode(self._dev_mode)
        try:
            try:
                LOGGER.debug(
                    "AUTH_FLOW[update_data]: starting update cycle, installation=%s",
                    self.installation_id,
                )
                authentication = await self.authentication_policy.authenticate()
                if not authentication.authenticated:
                    if authentication.cached_data:
                        LOGGER.warning("Login failed but using cached coordinator data")
                        return authentication.cached_data
                    raise UpdateFailed("Failed to login to My Verisure")

                LOGGER.info(
                    "Updating alarm and installation data for installation %s",
                    self.installation_id,
                )
                result = await self.snapshot_service.refresh(self.installation_id)
                if should_log_detailed():
                    LOGGER.debug(
                        "Coordinator snapshot (redacted): %s",
                        redact_sensitive_data(result),
                    )

                await self.refresh_effects.apply(
                    result,
                    self.installation_id,
                    create_dummy_images=True,
                )
                LOGGER.info(
                    "Alarm and installation data updated for installation %s",
                    self.installation_id,
                )
                return result

            except Exception as ex:
                failure = self._failure_classifier.classify(ex)
                LOGGER.error("Coordinator update failed (%s): %s", failure.kind, failure.message)
                if failure.kind is CoordinatorFailureKind.SERVICE_BLOCKED:
                    title = await self.get_translation("notifications.service.blocked.title")
                    message = await self.get_translation("notifications.service.blocked.message")
                    async_create(
                        self.hass,
                        message,
                        title=title,
                        notification_id="verisure_service_blocked",
                    )
                    cached_data = self.load_alarm_info()
                    if cached_data:
                        LOGGER.warning("Service blocked but using cached coordinator data")
                        return cached_data
                    raise UpdateFailed(
                        f"Service temporarily blocked: {failure.message}"
                    ) from ex
                if failure.kind is CoordinatorFailureKind.AUTHENTICATION:
                    raise ConfigEntryAuthFailed from ex
                raise UpdateFailed(
                    f"{failure.kind.replace('_', ' ').capitalize()}: {failure.message}"
                ) from ex
        finally:
            reset_dev_mode(tok)

    def load_alarm_info(self) -> Dict[str, Any]:
        """Load the last saved data from coordinator data file."""
        return self.snapshot_store.load()

    def get_alarm_info_info(self) -> Dict[str, Any]:
        """Get information about the last saved data file."""
        return self.snapshot_store.metadata()

    async def _async_execute_alarm_command(self, command_name: str) -> ArmResult | DisarmResult:
        """Execute one alarm command and apply HA-side effects."""
        command = COMMANDS[command_name]
        tok = set_dev_mode(self._dev_mode)
        try:
            panel, caps = self._panel_capabilities_from_stored_data()
            operation = getattr(self.alarm_use_case, command.operation)
            kwargs: dict[str, Any] = {"panel": panel, "capabilities": caps}
            if command.auto_arm_perimeter:
                kwargs["auto_arm_perimeter_with_internal"] = self.config_entry.options.get(
                    CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
                    self.config_entry.data.get(CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL, False),
                )
            result = await operation(self.installation_id, **kwargs)
            if result.success:
                await self._async_refresh_alarm_only()
                title = await self.get_translation("notifications.title.success")
                message = await self.get_translation(command.success_key)
                notification_id = f"{command.notification_id}_success"
            else:
                title = await self.get_translation("notifications.title.error")
                message = await self.get_translation(command.error_key, message=result.message)
                notification_id = f"{command.notification_id}_error"
            async_create(self.hass, message, title=title, notification_id=notification_id)
            return result
        except Exception as error:
            LOGGER.error("Failed to execute alarm command %s: %s", command_name, error)
            title = await self.get_translation("notifications.title.error")
            message = await self.get_translation(command.exception_key, error=str(error))
            async_create(
                self.hass,
                message,
                title=title,
                notification_id=f"{command.notification_id}_exception",
            )
            result_type = DisarmResult if command_name == "disarm" else ArmResult
            return result_type(success=False, message=f"Failed to {command_name}: {error}")
        finally:
            reset_dev_mode(tok)
    async def async_arm_away(self) -> ArmResult:
        """Arm the alarm in away mode."""
        return cast(ArmResult, await self._async_execute_alarm_command("arm_away"))

    async def async_arm_home(self) -> ArmResult:
        """Arm the alarm in home mode."""
        return cast(ArmResult, await self._async_execute_alarm_command("arm_home"))

    async def async_arm_night(self) -> ArmResult:
        """Arm the alarm in night mode."""
        return cast(ArmResult, await self._async_execute_alarm_command("arm_night"))

    async def async_disarm(self) -> DisarmResult:
        """Disarm the alarm."""
        return cast(DisarmResult, await self._async_execute_alarm_command("disarm"))

    async def async_refresh_camera_images(self) -> None:
        """Refresh camera images."""
        tok = set_dev_mode(self._dev_mode)
        try:
            LOGGER.info("Refreshing camera images for installation %s", self.installation_id)
            result = await self.refresh_camera_images_use_case.refresh_camera_images(
                installation_id=self.installation_id,
                max_attempts=30,
                check_interval=4,
            )

            LOGGER.info(
                "Camera images refresh completed: %d cameras, %d ok, %d failed",
                result.total_cameras,
                result.successful_refreshes,
                result.failed_refreshes,
            )
        except Exception as e:
            LOGGER.error("Failed to refresh camera images: %s", e)
        finally:
            reset_dev_mode(tok)

    async def get_translation(self, key: str, **kwargs: object) -> str:
        """Resolve one localized notification string."""
        return await self._translation_service.get(
            self.hass.config.language,
            key,
            **kwargs,
        )

    def has_valid_session(self) -> bool:
        """Check if we have a valid session."""
        try:
            return self.session_manager.is_session_valid()
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
        tok = set_dev_mode(self._dev_mode)
        try:
            await self.session_manager.async_load_session_from_disk()
            return (
                self.session_manager.is_session_valid()
                or self.session_manager.can_attempt_refresh()
            )
        except Exception as e:
            LOGGER.error("Error loading session: %s", e)
            return False
        finally:
            reset_dev_mode(tok)

    def register_alarm_control_panel(self, alarm_panel) -> None:
        """Register the alarm control panel for state updates."""
        self._alarm_control_panel = alarm_panel
        LOGGER.debug("Alarm control panel registered with coordinator")

    def clear_alarm_transition_state(self) -> None:
        """Clear the transition state of the registered alarm control panel."""
        if self._alarm_control_panel and hasattr(self._alarm_control_panel, 'clear_transition_state'):
            self._alarm_control_panel.clear_transition_state()
            LOGGER.debug("Cleared alarm control panel transition state")

    def register_button(self, button) -> None:
        """Register the button for state updates."""
        self._button = button
        LOGGER.debug("Button registered with coordinator")

    def clear_button_executing_state(self) -> None:
        """Clear the executing state of the registered button."""
        if self._button and hasattr(self._button, 'clear_executing_state'):
            self._button.clear_executing_state()
            LOGGER.debug("Cleared button executing state")

    async def async_cleanup(self):
        """Clean up resources."""
        try:
            LOGGER.warning("Coordinator cleanup completed")
        except Exception as e:
            LOGGER.error("Error during cleanup: %s", e) 
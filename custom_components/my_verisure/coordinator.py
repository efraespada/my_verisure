"""DataUpdateCoordinator for the My Verisure integration."""

from __future__ import annotations

import asyncio
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

from .core.application.exceptions import MyVerisureAuthenticationError, MyVerisureError
from .core.api.exceptions import MyVerisureServiceBlockedError
from .core.api.device_manager import DeviceManager
from .push import HomeAssistantPush, async_reconcile_profile
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
from .core.application.alarm_status_service import AlarmStatusService, KNOWN_PANEL_CODES
from .core.utils.jwt_utils import get_jwt_payload, is_jwt_expired
from .core.application.coordinator_snapshot_store import CoordinatorSnapshotStore
from .core.application.coordinator_refresh_effects import CoordinatorRefreshEffects
from .core.application.coordinator_camera_refresh import CoordinatorCameraRefresh
from .core.application.coordinator_notifications import CoordinatorNotificationService
from .core.application.coordinator_session_policy import (
    CoordinatorSessionPolicy,
    SessionAction,
)
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
    CONF_PUSH_ENABLED,
)
from .core.log_utils import redact_sensitive_data, reset_dev_mode, set_dev_mode, should_log_detailed
from .core.application.models.alarm import AlarmStatus, ArmResult, DisarmResult


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
        self.installation_id: str = cast(str, entry.data[CONF_INSTALLATION_ID])
        
        project_root = Path(hass.config.path(STORAGE_DIR)) / f"my_verisure_{entry.entry_id}"
        session_file = project_root / "data" / "session.json"

        self._push_enabled = bool(entry.options.get(CONF_PUSH_ENABLED, False))
        self.composition_root = composition_root or build_my_verisure_composition_root(
            project_root=project_root,
            **({"push_enabled": True} if self._push_enabled else {}),
        )
        self._push = (
            HomeAssistantPush(hass, self.composition_root)
            if self._push_enabled else None
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
        self.coordinator_camera_refresh = CoordinatorCameraRefresh(
            self.refresh_camera_images_use_case
        )

        self.session_manager = self.composition_root.get(SessionManager)
        self._installation_auth_hash: str | None = None
        self._camera_refresh_lock = asyncio.Lock()
        username = self.config_entry.data.get(CONF_USER)
        password = self.config_entry.data.get(CONF_PASSWORD)
        if isinstance(username, str) and isinstance(password, str):
            self.session_manager.set_login_credentials(username, password)
        self.file_manager = self.composition_root.get(FileManager)
        self.snapshot_store = CoordinatorSnapshotStore(self.file_manager)
        self.refresh_effects = CoordinatorRefreshEffects(
            self.snapshot_store,
            self.async_set_updated_data,
            self.create_dummy_camera_images_use_case,
        )
        self.authentication_policy = CoordinatorAuthenticationPolicy(
            login=self.async_login,
            load_cache=self.async_load_alarm_info,
        )
        
        # Reference to alarm control panel for state updates
        self._alarm_control_panel = None
        self._button = None
        self._failure_classifier = CoordinatorFailureClassifier()
        self._translation_service = TranslationService(Path(__file__).parent / "translations")
        self.notifications = CoordinatorNotificationService(
            self.get_translation,
            lambda message, *, title, notification_id: async_create(
                self.hass,
                message,
                title=title,
                notification_id=notification_id,
            ),
        )
        self.session_policy = CoordinatorSessionPolicy()

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
            config_entry=entry,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def async_login(self) -> bool:
        """Login to My Verisure with improved error handling and caching."""
        try:
            push = getattr(self, "_push", None)
            if push is not None:
                await push.async_prepare()
            decision = self.session_policy.decide(self.session_manager)
            LOGGER.debug(
                "AUTH_FLOW[async_login]: action=%s, authenticated=%s, valid=%s, blocked=%s, has_cache=%s",
                decision.action,
                decision.authenticated,
                decision.valid,
                decision.blocked,
                bool(await self.async_load_alarm_info()),
            )
            if decision.action is SessionAction.SKIP_BLOCKED:
                LOGGER.warning(
                    "Login skipped: service temporarily blocked (cooldown active) - "
                    "will use cached data if available"
                )
                return False

            if decision.action is SessionAction.USE_VALID_SESSION:
                LOGGER.debug("Using existing valid session")
                return True

            if decision.action is SessionAction.UNAVAILABLE:
                LOGGER.warning(
                    "Cannot attempt session refresh (authenticated=%s, blocked=%s, valid=%s)",
                    decision.authenticated,
                    decision.blocked,
                    decision.valid,
                )
                return False

            LOGGER.info("Session invalid, attempting automatic refresh...")
            return await self.async_refresh_session()

        except MyVerisureServiceBlockedError:
            LOGGER.error("Service temporarily blocked during login")
            # Send service blocked notification
            await self.notifications.notify(
                title_key="notifications.service.blocked.title",
                message_key="notifications.service.blocked.message",
                notification_id="verisure_service_blocked",
            )
            return False
        except asyncio.CancelledError:
            raise
        except MyVerisureError:
            raise
        except Exception:
            LOGGER.error("Login failed")
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
                
        except asyncio.CancelledError:
            raise
        except MyVerisureError:
            raise
        except Exception:
            LOGGER.error("Session refresh failed")
            raise MyVerisureError("Session refresh failed") from None

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

            panel, caps = await self._async_ensure_installation_context()
            if not panel or not caps:
                return await self._async_update_data()

            LOGGER.info("Refreshing alarm state")
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
            LOGGER.info("Alarm state refreshed")
            return result
        finally:
            reset_dev_mode(tok)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via My Verisure API."""
        tok = set_dev_mode(self._dev_mode)
        try:
            try:
                LOGGER.debug("AUTH_FLOW[update_data]: starting update cycle")
                authentication = await self.authentication_policy.authenticate()
                if not authentication.authenticated:
                    if authentication.cached_data:
                        LOGGER.warning("Login failed but using cached coordinator data")
                        return authentication.cached_data
                    raise UpdateFailed("Failed to login to My Verisure")

                LOGGER.info("Updating alarm and installation data")
                snapshot_auth_hash = self.get_session_hash()
                result = await self.snapshot_service.refresh(self.installation_id)
                if snapshot_auth_hash != self.get_session_hash():
                    raise MyVerisureError("Session changed while loading installation")
                self._installation_auth_hash = snapshot_auth_hash
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
                LOGGER.info("Alarm and installation data updated")
                return result

            except asyncio.CancelledError:
                raise
            except Exception as ex:
                failure = self._failure_classifier.classify(ex)
                LOGGER.error("Coordinator update failed (%s)", failure.kind)
                if failure.kind is CoordinatorFailureKind.SERVICE_BLOCKED:
                    await self.notifications.notify(
                        title_key="notifications.service.blocked.title",
                        message_key="notifications.service.blocked.message",
                        notification_id="verisure_service_blocked",
                    )
                    cached_data = await self.async_load_alarm_info()
                    if cached_data:
                        LOGGER.warning("Service blocked but using cached coordinator data")
                        return cached_data
                    raise UpdateFailed("Service temporarily blocked") from None
                if failure.kind is CoordinatorFailureKind.AUTHENTICATION:
                    raise ConfigEntryAuthFailed from None
                if isinstance(ex, MyVerisureError):
                    raise
                raise UpdateFailed(failure.message) from None
        finally:
            reset_dev_mode(tok)

    def load_alarm_info(self) -> Dict[str, Any]:
        """Load the last saved data from coordinator data file."""
        return self.snapshot_store.load()

    async def async_load_alarm_info(self) -> Dict[str, Any]:
        """Load the last saved data without blocking the event loop."""
        return await asyncio.to_thread(self.load_alarm_info)

    def get_alarm_info_info(self) -> Dict[str, Any]:
        """Get information about the last saved data file."""
        return self.snapshot_store.metadata()

    async def _async_ensure_installation_context(self) -> tuple[str, str]:
        """Bind installation permissions to the current authenticated session."""
        current_hash = self.get_session_hash()
        if not current_hash:
            raise MyVerisureAuthenticationError("Authenticated session unavailable")
        panel, caps = self._panel_capabilities_from_stored_data()
        claims = get_jwt_payload(caps) if caps else None
        expired = bool(caps and claims is not None and is_jwt_expired(caps))
        if self._installation_auth_hash == current_hash and panel and caps and not expired:
            return panel, caps

        LOGGER.info("Refreshing installation permissions for the current session")
        detailed = await self.installation_use_case.get_installation_services(self.installation_id)
        panel = detailed.installation.panel
        caps = detailed.installation.capabilities
        if not panel or not caps:
            raise MyVerisureError("Installation context unavailable")
        if current_hash != self.get_session_hash():
            raise MyVerisureError("Session changed while loading installation permissions")
        self.data = {**(self.data or {}), "detailed_installation": detailed.dict()}
        self._installation_auth_hash = current_hash
        return panel, caps

    async def _async_execute_alarm_command(self, command_name: str) -> ArmResult | DisarmResult:
        """Execute one alarm command and apply HA-side effects."""
        command = COMMANDS[command_name]
        tok = set_dev_mode(self._dev_mode)
        command_started = False
        try:
            if not await self.async_login():
                raise MyVerisureAuthenticationError("Authenticated session unavailable")
            panel, caps = await self._async_ensure_installation_context()
            operation = getattr(self.alarm_use_case, command.operation)
            kwargs: dict[str, Any] = {"panel": panel, "capabilities": caps}
            if command.auto_arm_perimeter:
                kwargs["auto_arm_perimeter_with_internal"] = self.config_entry.options.get(
                    CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
                    self.config_entry.data.get(CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL, False),
                )
            command_started = True
            result = await operation(self.installation_id, **kwargs)
            await self._async_apply_command_state(result)
            command_started = False
            if result.success:
                if result.confirmed_state not in KNOWN_PANEL_CODES:
                    # Preserve support for other configured modes without
                    # guessing a raw panel code. A failed follow-up read must
                    # not turn an already confirmed command into a failed one.
                    try:
                        await self._async_refresh_alarm_only()
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        LOGGER.warning("Command confirmed; panel state refresh unavailable")
                await self.notifications.notify(
                    title_key="notifications.title.success",
                    message_key=command.success_key,
                    notification_id=f"{command.notification_id}_success",
                )
            else:
                await self.notifications.notify(
                    title_key="notifications.title.error",
                    message_key=command.error_key,
                    notification_id=f"{command.notification_id}_error",
                    message_args={"message": "Alarm operation was rejected"},
                )
            return result
        except MyVerisureError:
            if command_started:
                await self._async_apply_command_state(ArmResult(False, "Command not confirmed"))
            raise
        except Exception as error:
            if command_started:
                await self._async_apply_command_state(ArmResult(False, "Command not confirmed"))
            LOGGER.error("Failed to execute alarm command %s", command_name)
            await self.notifications.notify(
                title_key="notifications.title.error",
                message_key=command.exception_key,
                notification_id=f"{command.notification_id}_exception",
                message_args={"error": "Alarm operation failed"},
            )
            result_type = DisarmResult if command_name == "disarm" else ArmResult
            return result_type(success=False, message="Alarm operation failed")
        finally:
            reset_dev_mode(tok)

    async def _async_apply_command_state(self, result: ArmResult | DisarmResult) -> None:
        """Publish the panel's completion response without another radio request."""
        code = result.confirmed_state if result.success else None
        data = AlarmStatusService.from_panel_code(code)
        known = code in KNOWN_PANEL_CODES
        status = AlarmStatus(
            success=known,
            message="Panel state confirmed" if known else "Alarm status unknown",
            status=("OK" if code == "D" else "ALARM") if known else None,
            data=data,
        )
        snapshot = merge_alarm_snapshot(
            installation_id=self.installation_id,
            alarm_status=status.dict(),
            detailed_installation=(self.data or {}).get("detailed_installation", {}),
            timestamp=time.time(),
        )
        await self.refresh_effects.apply(snapshot, self.installation_id, create_dummy_images=False)
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

    async def async_refresh_camera_images(self, camera_identifier: str | None = None) -> None:
        """Refresh camera images."""
        if self._camera_refresh_lock.locked():
            raise MyVerisureError("Camera image refresh already running")
        tok = set_dev_mode(self._dev_mode)
        try:
            async with self._camera_refresh_lock:
                if not await self.async_login():
                    raise MyVerisureAuthenticationError("Authenticated session unavailable")
                if camera_identifier is None:
                    result = await self.coordinator_camera_refresh.run(self.installation_id)
                else:
                    result = await self.coordinator_camera_refresh.run(
                        self.installation_id, camera_identifier=camera_identifier
                    )
                if result.failed_refreshes:
                    raise MyVerisureError("Camera images could not all be refreshed")
                self.async_update_listeners()
        except asyncio.CancelledError:
            raise
        except MyVerisureError:
            raise
        except Exception:
            LOGGER.error("Failed to refresh camera images")
            raise MyVerisureError("Camera image refresh failed") from None
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
            await async_reconcile_profile(
                self.composition_root.get(DeviceManager), self.session_manager
            )
            return (
                self.session_manager.is_session_valid()
                or self.session_manager.can_attempt_refresh()
            )
        except Exception:
            LOGGER.error("Error loading session")
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

    async def async_cleanup(self) -> None:
        """Cancel scheduled coordinator work and release entry-local references."""
        try:
            push = getattr(self, "_push", None)
            if push is not None:
                await push.async_stop()
            await self.async_shutdown()
            self._alarm_control_panel = None
            self._button = None
            LOGGER.debug("Coordinator cleanup completed")
        except Exception:
            LOGGER.error("Error during coordinator cleanup")

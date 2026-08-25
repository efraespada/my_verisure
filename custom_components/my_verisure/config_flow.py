"""Config flow for My Verisure integration."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .core.application.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureError,
    MyVerisureOTPError,
    MyVerisurePersistenceError,
    MyVerisureTimeoutError,
)
from homeassistant.helpers.storage import STORAGE_DIR

from .core.dependency_injection.composition_root import (
    CompositionRoot,
    build_my_verisure_composition_root,
)
from .core.file_manager import FileManager
from .core.use_cases.interfaces.auth_use_case import AuthUseCase
from .core.use_cases.interfaces.installation_use_case import InstallationUseCase
from .core.use_cases.interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase
from .core.session_manager import SessionManager
from .core.application.otp_code_policy import is_valid_otp_code
from .core.application.auth_flow_transactions import AuthFlowTransactionService
from .core.application.models.camera_refresh import CameraRefresh
from .core.const import (
    CONF_USER,
    CONF_PASSWORD,
    CONF_INSTALLATION_ID,
    CONF_PHONE_ID,
    CONF_OTP_CODE,
    DOMAIN,
    LOGGER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
    CONF_DEV_MODE,
)


class MyVerisureConfigFlowHandler(
    ConfigFlow, domain=DOMAIN  # type: ignore[call-arg]  # HA registers domain via __init_subclass__
):
    """Handle a config flow for My Verisure."""

    VERSION = 1

    user: str
    password: str
    auth_use_case: Any
    session_manager: Any
    installation_use_case: Any
    composition_root: CompositionRoot | None = None
    _otp_error: bool = False
    _otp_phones: list[dict[str, Any]] = []
    _installations: list[Any] = []
    _reauth_mode: bool = False

    def __init__(self) -> None:
        """Initialize isolated mutable state for one config flow instance."""
        super().__init__()
        self._otp_phones = []
        self._installations = []
        self._reauth_session_snapshot: dict[str, object] | None = None
        self._reauth_session_bytes: bytes | None = None
        self._reauth_entry_data: dict[str, Any] | None = None
        self._auth_flow_transactions = AuthFlowTransactionService()

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Expose only a short suffix of a phone in the HA form."""
        digits = "".join(character for character in phone if character.isdigit())
        return f"••••{digits[-2:]}" if len(digits) >= 2 else "[REDACTED]"

    async def _async_cleanup_initial_flow(self) -> bool:
        """Delegate entry-scoped cleanup to the application transaction service."""
        if self.context.get("entry_id") is not None or self.composition_root is None:
            return True
        file_manager = self.composition_root.get(FileManager)
        session_manager = getattr(self, "session_manager", None)
        return await self._auth_flow_transactions.cleanup_initial_flow(
            file_manager, session_manager
        )

    async def _async_abort_with_cleanup(self, reason: str) -> ConfigFlowResult:
        """Verify cleanup before returning a terminal flow result."""
        if not await self._async_cleanup_initial_flow():
            LOGGER.error("Could not confirm initial-flow cleanup")
            reason = "cannot_persist"
        return super().async_abort(reason=reason)

    async def _async_cleanup_after_initial_error(self) -> ConfigFlowResult | None:
        """Confirm cleanup before redisplaying an initial-flow form."""
        if self.context.get("entry_id") is not None:
            return None
        if not await self._async_cleanup_initial_flow():
            LOGGER.error("Could not confirm initial-flow cleanup")
            return await self._async_abort_with_cleanup(reason="cannot_persist")
        return None

    def _reset_initial_flow_runtime(self) -> None:
        """Drop references to an entry-scoped runtime after initial cleanup."""
        self.composition_root = None
        self.auth_use_case = None
        self.session_manager = None
        self.installation_use_case = None

    def _ensure_composition(self) -> CompositionRoot:
        """Create the isolated composition used by this configuration flow."""
        if self.composition_root is None:
            entry_id = self.context.get("entry_id")
            session_identity = (
                str(entry_id) if entry_id else f"flow_{self.flow_id}"
            )
            project_root = Path(self.hass.config.path(STORAGE_DIR)) / f"my_verisure_{session_identity}"
            self.composition_root = build_my_verisure_composition_root(
                project_root=project_root,
            )
        return self.composition_root

    async def _async_ensure_composition(self) -> CompositionRoot:
        """Build the composition without blocking the Home Assistant event loop."""
        return await self.hass.async_add_executor_job(self._ensure_composition)

    async def _async_get_available_phones(self) -> list[dict[str, Any]]:
        """Read phone destinations off the Home Assistant event loop."""
        try:
            return await self.hass.async_add_executor_job(
                self.auth_use_case.get_available_phones
            )
        except BaseException:
            self.auth_use_case.invalidate_otp_challenge()
            raise

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MyVerisureOptionsFlowHandler:
        """Get the options flow for this handler."""
        return MyVerisureOptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.user = user_input[CONF_USER]
            self.password = user_input[CONF_PASSWORD]
            
            root = await self._async_ensure_composition()
            self.auth_use_case = root.get(AuthUseCase)
            self.session_manager = root.get(SessionManager)
            self.installation_use_case = root.get(InstallationUseCase)

            try:
                # Perform login using auth use case
                auth_result = await self.auth_use_case.login(self.user, self.password)
                
                if auth_result.success:
                    return await self.async_step_installation()
                else:
                    errors["base"] = "invalid_auth"

            except MyVerisureAuthenticationError:
                LOGGER.warning("Invalid credentials for My Verisure")
                errors["base"] = "invalid_auth"
            except MyVerisureTimeoutError:
                LOGGER.warning("Authentication request timed out")
                errors["base"] = "cannot_connect"
            except MyVerisureConnectionError:
                LOGGER.warning("Connection error to My Verisure")
                errors["base"] = "cannot_connect"
            except MyVerisurePersistenceError:
                LOGGER.error("Authentication session could not be persisted")
                errors["base"] = "cannot_persist"
            except MyVerisureOTPError:
                LOGGER.warning("OTP authentication required")
                self._otp_error = True
                return await self.async_step_phone_selection()
            except MyVerisureError:
                LOGGER.warning("Unexpected authentication error")
                errors["base"] = "unknown"
            # Authentication errors must clear temporary flow artifacts before retry.
            if errors:
                cleanup_result = await self._async_cleanup_after_initial_error()
                if cleanup_result is not None:
                    return cleanup_result
                self._reset_initial_flow_runtime()

            # Don't clear dependencies here - they're needed for the next step

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USER): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_phone_selection(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle phone selection for OTP."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                phone_id = int(user_input[CONF_PHONE_ID])
                phones = self._otp_phones or [
                    dict(phone)
                    for phone in await self._async_get_available_phones()
                ]
                selected_phone = next(
                    (phone for phone in phones if int(phone.get("id", -1)) == phone_id),
                    None,
                )
                if selected_phone is None:
                    errors["base"] = "otp_invalid_phone"
                elif not self.auth_use_case.select_phone(phone_id):
                    errors["base"] = "otp_invalid_phone"
                else:
                    record_id = selected_phone.get("record_id")
                    if (
                        isinstance(record_id, bool)
                        or not isinstance(record_id, int)
                        or record_id <= 0
                    ):
                        errors["base"] = "otp_data_missing"
                    elif await self.auth_use_case.send_otp(record_id):
                        return await self.async_step_otp_verification()
                    else:
                        errors["base"] = "otp_failed"
            except asyncio.CancelledError:
                self.auth_use_case.invalidate_otp_challenge()
                raise
            except MyVerisureTimeoutError:
                self.auth_use_case.invalidate_otp_challenge()
                LOGGER.warning("Authentication request timed out")
                errors["base"] = "cannot_connect"
            except MyVerisureConnectionError:
                self.auth_use_case.invalidate_otp_challenge()
                errors["base"] = "cannot_connect"
            except MyVerisureOTPError:
                self.auth_use_case.invalidate_otp_challenge()
                errors["base"] = "otp_failed"
            except (TypeError, ValueError, KeyError):
                self.auth_use_case.invalidate_otp_challenge()
                errors["base"] = "otp_invalid_phone"
            except Exception:
                self.auth_use_case.invalidate_otp_challenge()
                LOGGER.error("OTP phone selection failed")
                errors["base"] = "unknown"

        try:
            phones = [
                dict(phone)
                for phone in await self._async_get_available_phones()
            ]
            self._otp_phones = phones
            if not phones:
                LOGGER.error("No phone numbers available for required OTP")
                return self.async_show_form(
                    step_id="phone_selection",
                    data_schema=vol.Schema({}),
                    errors={"base": "otp_no_phone_destinations"},
                )

            phone_options = {
                str(phone["id"]): self._mask_phone(str(phone.get("phone", "")))
                for phone in phones
                if phone.get("id") is not None
            }
            if not phone_options:
                return self.async_show_form(
                    step_id="phone_selection",
                    data_schema=vol.Schema({}),
                    errors={"base": "otp_no_phone_destinations"},
                )
        except asyncio.CancelledError:
            self.auth_use_case.invalidate_otp_challenge()
            raise
        except MyVerisureConnectionError:
            return self.async_show_form(
                step_id="phone_selection",
                data_schema=vol.Schema({}),
                errors={"base": "cannot_connect"},
            )
        except MyVerisureError:
            return self.async_show_form(
                step_id="phone_selection",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
            )
        except Exception:
            LOGGER.error("OTP phone lookup failed")
            return self.async_show_form(
                step_id="phone_selection",
                data_schema=vol.Schema({}),
                errors={"base": "unknown"},
            )

        return self.async_show_form(
            step_id="phone_selection",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE_ID): vol.In(phone_options),
                }
            ),
            errors=errors,
        )

    async def async_step_otp_verification(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle OTP verification."""
        errors: dict[str, str] = {}

        if user_input is not None:
            otp_code = user_input[CONF_OTP_CODE]

            if not is_valid_otp_code(otp_code):
                self.auth_use_case.invalidate_otp_challenge()
                errors["base"] = "otp_invalid"
                return self.async_show_form(
                    step_id="otp_verification",
                    data_schema=vol.Schema({vol.Required(CONF_OTP_CODE): str}),
                    errors=errors,
                )

            try:
                auth_result = await self.auth_use_case.verify_otp(otp_code)
                if auth_result.success:
                    self.session_manager = (await self._async_ensure_composition()).get(
                        SessionManager
                    )
                    if self._reauth_mode:
                        return await self._finish_reauthentication()
                    if not self.session_manager.is_session_valid():
                        if not await self._auth_flow_transactions.async_fail_closed_reauthentication(
                            self.session_manager
                        ):
                            errors["base"] = "cannot_persist"
                        else:
                            errors["base"] = "authentication_required"
                    else:
                        return await self.async_step_installation()
                else:
                    errors["base"] = "otp_invalid"
            except MyVerisureAuthenticationError:
                rollback_result = await self._rollback_or_abort_reauthentication() if self._reauth_mode else None
                if rollback_result is not None:
                    return rollback_result
                errors["base"] = "authentication_required"
            except MyVerisureDeviceAuthorizationError:
                rollback_result = await self._rollback_or_abort_reauthentication() if self._reauth_mode else None
                if rollback_result is not None:
                    return rollback_result
                errors["base"] = "authentication_required"
            except MyVerisureOTPError as error:
                if self._reauth_mode and not error.retryable:
                    rollback_result = await self._rollback_or_abort_reauthentication()
                    if rollback_result is not None:
                        return rollback_result
                errors["base"] = "otp_invalid"
            except MyVerisureTimeoutError:
                rollback_result = await self._rollback_or_abort_reauthentication() if self._reauth_mode else None
                if rollback_result is not None:
                    return rollback_result
                LOGGER.warning("Authentication request timed out")
                errors["base"] = "cannot_connect"
            except MyVerisureConnectionError:
                rollback_result = await self._rollback_or_abort_reauthentication() if self._reauth_mode else None
                if rollback_result is not None:
                    return rollback_result
                errors["base"] = "cannot_connect"
            except MyVerisurePersistenceError:
                rollback_result = await self._rollback_or_abort_reauthentication() if self._reauth_mode else None
                if rollback_result is not None:
                    return rollback_result
                LOGGER.error("Authentication session could not be persisted")
                errors["base"] = "cannot_persist"
                if not self._reauth_mode:
                    cleanup_result = await self._async_cleanup_after_initial_error()
                    if cleanup_result is not None:
                        return cleanup_result
                    self._reset_initial_flow_runtime()
                    return await self.async_step_user()
            except asyncio.CancelledError as cancellation:
                if self._reauth_mode:
                    try:
                        await self._rollback_or_abort_reauthentication(
                            preserve_cancellation=True
                        )
                    except BaseException as rollback_error:
                        raise cancellation from rollback_error
                else:
                    try:
                        if not await self._async_cleanup_initial_flow():
                            raise RuntimeError("initial-flow cleanup could not be confirmed")
                        self._reset_initial_flow_runtime()
                    except BaseException as cleanup_error:
                        raise cancellation from cleanup_error
                raise
            except Exception:
                rollback_result = await self._rollback_or_abort_reauthentication() if self._reauth_mode else None
                if rollback_result is not None:
                    return rollback_result
                LOGGER.error("OTP verification failed")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="otp_verification",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OTP_CODE): str,
                }
            ),
            errors=errors,
        )

    async def async_step_installation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle installation selection after confirmed authentication."""
        errors: dict[str, str] = {}
        session_manager = (await self._async_ensure_composition()).get(SessionManager)
        self.session_manager = session_manager
        self.installation_use_case = (await self._async_ensure_composition()).get(
            InstallationUseCase
        )

        if not session_manager.is_session_valid():
            return self.async_show_form(
                step_id="installation",
                data_schema=vol.Schema({}),
                errors={"base": "authentication_required"},
            )

        if user_input is not None:
            installation_id = user_input[CONF_INSTALLATION_ID]
            try:
                installations = await self.installation_use_case.get_installations()
                self._installations = list(installations)
                installation = next(
                    (inst for inst in installations if inst.numinst == installation_id),
                    None,
                )

                if installation:
                    create_dummy_camera_images_use_case = (await self._async_ensure_composition()).get(
                        CreateDummyCameraImagesUseCase
                    )
                    camera_refresh = (
                        await create_dummy_camera_images_use_case.create_dummy_camera_images(
                            installation_id=installation_id,
                        )
                    )
                    if not (
                        isinstance(camera_refresh, CameraRefresh)
                        and camera_refresh.failed_refreshes == 0
                        and camera_refresh.successful_refreshes
                        == camera_refresh.total_cameras
                    ):
                        LOGGER.error("Initial camera persistence was incomplete")
                        cleanup_result = await self._async_cleanup_after_initial_error()
                        if cleanup_result is not None:
                            return cleanup_result
                        if self.context.get("entry_id") is None:
                            self._reset_initial_flow_runtime()
                            return await self.async_step_user()
                        errors["base"] = "cannot_persist"
                    elif self.context.get("entry_id") is None:
                        if not await self._async_cleanup_initial_flow():
                            LOGGER.error("Could not confirm initial-flow cleanup")
                            return await self._async_abort_with_cleanup(
                                reason="cannot_persist"
                            )
                        return self.async_create_entry(
                            title="My Verisure",
                            data={
                                CONF_USER: self.user,
                                CONF_PASSWORD: self.password,
                                CONF_INSTALLATION_ID: installation_id,
                                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                            },
                        )
                    elif self.context.get("entry_id") is not None:
                        return self.async_create_entry(
                            title="My Verisure",
                            data={
                                CONF_USER: self.user,
                                CONF_PASSWORD: self.password,
                                CONF_INSTALLATION_ID: installation_id,
                                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                            },
                        )
                if not installation:
                    errors["base"] = "installation_not_found"
            except MyVerisureTimeoutError:
                cleanup_result = await self._async_cleanup_after_initial_error()
                if cleanup_result is not None:
                    return cleanup_result
                LOGGER.warning("Authentication request timed out")
                errors["base"] = "cannot_connect"
            except MyVerisureConnectionError:
                cleanup_result = await self._async_cleanup_after_initial_error()
                if cleanup_result is not None:
                    return cleanup_result
                errors["base"] = "cannot_connect"
            except MyVerisureError:
                cleanup_result = await self._async_cleanup_after_initial_error()
                if cleanup_result is not None:
                    return cleanup_result
                errors["base"] = "unknown"
            except Exception:
                cleanup_result = await self._async_cleanup_after_initial_error()
                if cleanup_result is not None:
                    return cleanup_result
                LOGGER.error("Installation selection failed")
                errors["base"] = "unknown"

        try:
            installations = await self.installation_use_case.get_installations()
            self._installations = list(installations)
        except MyVerisureConnectionError:
            installations = []
            errors["base"] = "cannot_connect"
        except MyVerisureError:
            installations = []
            errors["base"] = "unknown"
        except Exception:
            LOGGER.error("Installation lookup failed")
            installations = []
            errors["base"] = "unknown"

        installation_options = {
            inst.numinst: f"Instalación {index + 1}"
            for index, inst in enumerate(installations)
        }

        return self.async_show_form(
            step_id="installation",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_INSTALLATION_ID): vol.In(installation_options),
                }
            ),
            errors=errors,
        )

    async def _rollback_reauthentication(
        self, existing_entry: ConfigEntry, previous_data: dict[str, Any]
    ) -> None:
        """Delegate reauthentication rollback and confirmation."""
        await self._auth_flow_transactions.rollback_reauthentication(
            entry=existing_entry,
            previous_data=dict(self._reauth_entry_data or previous_data),
            session=self.session_manager,
            session_snapshot=self._reauth_session_snapshot,
            session_bytes=self._reauth_session_bytes,
            update_entry=self.hass.config_entries.async_update_entry,
            reload_entry=self.hass.config_entries.async_reload,
            get_entry=self.hass.config_entries.async_get_entry,
        )

    async def _rollback_or_abort_reauthentication(
        self, *, preserve_cancellation: bool = False
    ) -> ConfigFlowResult | None:
        """Rollback a reauth failure, using confirmed cleanup if needed."""
        existing_entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if existing_entry is None:
            if preserve_cancellation:
                raise RuntimeError("reauthentication entry is unavailable")
            return await self._async_abort_with_cleanup(reason="cannot_persist")
        try:
            await asyncio.shield(
                self._rollback_reauthentication(existing_entry, dict(existing_entry.data))
            )
        except asyncio.CancelledError:
            raise
        except BaseException as rollback_error:
            try:
                safe = await asyncio.shield(
                    self._auth_flow_transactions.async_fail_closed_reauthentication(
                        self.session_manager
                    )
                )
            except BaseException:
                if preserve_cancellation:
                    raise
                LOGGER.error("Could not confirm reauthentication cleanup")
                return await self._async_abort_with_cleanup(reason="cannot_persist")
            if not safe:
                if preserve_cancellation:
                    raise RuntimeError(
                        "Reauthentication cleanup could not be confirmed"
                    ) from rollback_error
                LOGGER.error("Could not confirm reauthentication cleanup")
                return await self._async_abort_with_cleanup(reason="cannot_persist")
            if preserve_cancellation:
                return None
            LOGGER.error("Could not confirm reauthentication rollback")
            return await self._async_abort_with_cleanup(reason="cannot_persist")
        return None

    async def _finish_reauthentication(self) -> ConfigFlowResult:
        """Commit reauthentication through the application transaction service."""
        session_manager = (await self._async_ensure_composition()).get(SessionManager)
        existing_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        if existing_entry is None:
            return await self._async_abort_with_cleanup(reason="cannot_persist")
        if not session_manager.is_session_valid():
            try:
                await asyncio.shield(
                    self._rollback_reauthentication(existing_entry, dict(existing_entry.data))
                )
            except asyncio.CancelledError:
                raise
            except BaseException:
                LOGGER.error("Could not confirm invalid-session rollback")
                return await self._async_abort_with_cleanup(reason="cannot_persist")
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USER, default=self.user): str,
                        vol.Required(CONF_PASSWORD): str,
                    }
                ),
                errors={"base": "authentication_required"},
            )

        previous_data = dict(self._reauth_entry_data or existing_entry.data)
        updated_data = {
            **previous_data,
            CONF_USER: self.user,
            CONF_PASSWORD: self.password,
        }
        try:
            committed = await self._auth_flow_transactions.commit_reauthentication(
                entry=existing_entry,
                updated_data=updated_data,
                previous_data=previous_data,
                session=session_manager,
                session_snapshot=self._reauth_session_snapshot,
                session_bytes=self._reauth_session_bytes,
                update_entry=self.hass.config_entries.async_update_entry,
                reload_entry=self.hass.config_entries.async_reload,
                get_entry=self.hass.config_entries.async_get_entry,
            )
        except asyncio.CancelledError:
            raise
        except BaseException:
            LOGGER.error("Could not confirm reauthentication rollback")
            return await self._async_abort_with_cleanup(reason="cannot_persist")
        if not committed:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_USER, default=self.user): str,
                        vol.Required(CONF_PASSWORD): str,
                    }
                ),
                errors={"base": "cannot_persist"},
            )
        return await self._async_abort_with_cleanup(reason="reauth_successful")

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start the re-authentication form for an existing entry."""
        existing_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        if existing_entry is None:
            return await self._async_abort_with_cleanup(reason="unknown")

        self.user = existing_entry.data[CONF_USER]
        self.password = existing_entry.data[CONF_PASSWORD]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authenticate updated credentials, including the complete OTP flow."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.user = user_input[CONF_USER]
            self.password = user_input[CONF_PASSWORD]
            self._reauth_mode = True
            root = await self._async_ensure_composition()
            self.auth_use_case = root.get(AuthUseCase)
            self.session_manager = root.get(SessionManager)
            await self.session_manager.async_load_session_from_disk()

            entry_for_snapshot = self.hass.config_entries.async_get_entry(
                self.context["entry_id"]
            )
            if entry_for_snapshot is None:
                return await self._async_abort_with_cleanup(reason="cannot_persist")
            self._reauth_entry_data = dict(entry_for_snapshot.data)
            try:
                (
                    self._reauth_session_snapshot,
                    self._reauth_session_bytes,
                ) = await self.session_manager.async_capture_transaction_state()
                auth_result = await self.auth_use_case.login(self.user, self.password)
                if auth_result.success:
                    if self.session_manager.is_session_valid():
                        return await self._finish_reauthentication()
                    existing_entry = self.hass.config_entries.async_get_entry(
                        self.context["entry_id"]
                    )
                    if existing_entry is None:
                        return await self._async_abort_with_cleanup(reason="cannot_persist")
                    try:
                        await asyncio.shield(
                            self._rollback_reauthentication(
                                existing_entry, self._reauth_entry_data or {}
                            )
                        )
                    except asyncio.CancelledError:
                        raise
                    except BaseException:
                        LOGGER.error("Could not confirm invalid-session rollback")
                        return await self._async_abort_with_cleanup(reason="cannot_persist")
                    errors["base"] = "authentication_required"
                else:
                    rollback_result = await self._rollback_or_abort_reauthentication()
                    if rollback_result is not None:
                        return rollback_result
                    errors["base"] = "invalid_auth"
            except asyncio.CancelledError as cancellation:
                try:
                    rollback_result = await self._rollback_or_abort_reauthentication(
                        preserve_cancellation=True
                    )
                except BaseException as rollback_error:
                    raise cancellation from rollback_error
                if rollback_result is not None:
                    return rollback_result
                raise
            except MyVerisureAuthenticationError:
                rollback_result = await self._rollback_or_abort_reauthentication()
                if rollback_result is not None:
                    return rollback_result
                errors["base"] = "invalid_auth"
            except MyVerisureTimeoutError:
                rollback_result = await self._rollback_or_abort_reauthentication()
                if rollback_result is not None:
                    return rollback_result
                LOGGER.warning("Authentication request timed out")
                errors["base"] = "cannot_connect"
            except MyVerisureConnectionError:
                rollback_result = await self._rollback_or_abort_reauthentication()
                if rollback_result is not None:
                    return rollback_result
                errors["base"] = "cannot_connect"
            except MyVerisureOTPError:
                self._otp_error = True
                return await self.async_step_phone_selection()
            except MyVerisurePersistenceError:
                rollback_result = await self._rollback_or_abort_reauthentication()
                if rollback_result is not None:
                    return rollback_result
                LOGGER.error("Authentication session could not be persisted")
                errors["base"] = "cannot_persist"
            except MyVerisureError:
                rollback_result = await self._rollback_or_abort_reauthentication()
                if rollback_result is not None:
                    return rollback_result
                LOGGER.warning("Unexpected error during reauthentication")
                errors["base"] = "unknown"
            except Exception:
                rollback_result = await self._rollback_or_abort_reauthentication()
                if rollback_result is not None:
                    return rollback_result
                LOGGER.error("Reauthentication failed")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USER, default=self.user): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class MyVerisureOptionsFlowHandler(OptionsFlow):
    """Handle My Verisure options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(CONF_SCAN_INTERVAL, self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)),
                    ): int,
                    vol.Optional(
                        CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
                        default=self.config_entry.options.get(CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL, False),
                    ): bool,
                    vol.Optional(
                        CONF_DEV_MODE,
                        default=self.config_entry.options.get(CONF_DEV_MODE, False),
                    ): bool,
                }
            ),
        )
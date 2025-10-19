"""Config flow for My Verisure integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import callback

from .core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
)
from .core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    get_installation_use_case,
    clear_dependencies,
    get_create_dummy_camera_images_use_case,
)
from .core.session_manager import get_session_manager
from .core.const import (
    CONF_INSTALLATION_ID,
    CONF_USER,
    CONF_PHONE_ID,
    CONF_OTP_CODE,
    DOMAIN,
    LOGGER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
)


class MyVerisureConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Verisure."""

    VERSION = 1

    user: str
    password: str
    auth_use_case: Any
    session_manager: Any
    installation_use_case: Any
    _otp_error: bool = False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> MyVerisureOptionsFlowHandler:
        """Get the options flow for this handler."""
        return MyVerisureOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.user = user_input[CONF_USER]
            self.password = user_input[CONF_PASSWORD]
            
            # Setup dependencies (no credentials needed, clients will get them from SessionManager)
            setup_dependencies()
            
            # Get use cases
            self.auth_use_case = get_auth_use_case()
            self.session_manager = get_session_manager()
            self.installation_use_case = get_installation_use_case()
            
            # Set credentials in session manager
            self.session_manager.update_credentials(
                self.user,
                self.password,
                "",  # hash_token will be set after login
                ""   # refresh_token will be set after login
            )

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
            except MyVerisureConnectionError:
                LOGGER.warning("Connection error to My Verisure")
                errors["base"] = "cannot_connect"
            except MyVerisureOTPError:
                LOGGER.warning("OTP authentication required")
                # Store OTP error for later use
                self._otp_error = True
                # Check if we have phone numbers available
                try:
                    LOGGER.warning("Attempting to get available phones after OTP error")
                    phones = self.auth_use_case.get_available_phones()
                    LOGGER.warning("Got %d phones from auth use case", len(phones))
                    if phones:
                        return await self.async_step_phone_selection()
                    else:
                        LOGGER.warning("No phone numbers available for OTP - device may already be authorized")
                        # If no phones available, it might mean device is already authorized
                        # Try to proceed with installation selection
                        return await self.async_step_installation()
                except Exception as e:
                    LOGGER.error("Error getting available phones: %s", e)
                    # If we can't get phones, try to proceed anyway
                    LOGGER.warning("Proceeding without OTP - device may already be authorized")
                    return await self.async_step_installation()
            except MyVerisureError as ex:
                LOGGER.warning("Unexpected error from My Verisure: %s", ex)
                errors["base"] = "unknown"
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
            phone_id = int(user_input[CONF_PHONE_ID])  # Convert to int
            LOGGER.warning("Selected phone ID: %d", phone_id)
            
            try:
                # Select phone and send OTP
                if self.auth_use_case.select_phone(phone_id):
                    # Get OTP hash from the stored OTP data
                    otp_data = self.auth_use_case._otp_data
                    if isinstance(otp_data, dict) and "otp_hash" in otp_data:
                        otp_hash = otp_data["otp_hash"]
                        LOGGER.warning("Using OTP hash from stored data: %s", otp_hash[:50] + "..." if otp_hash else "None")
                        otp_sent = await self.auth_use_case.send_otp(phone_id, otp_hash)
                        if otp_sent:
                            return await self.async_step_otp_verification()
                        else:
                            errors["base"] = "otp_send_failed"
                    else:
                        LOGGER.error("No OTP hash found in stored data: %s", otp_data)
                        errors["base"] = "otp_data_missing"
                else:
                    errors["base"] = "phone_selection_failed"
            except Exception as e:
                LOGGER.error("Error in phone selection: %s", e)
                errors["base"] = "unknown"
            # Don't clear dependencies here - they're needed for the next step

        try:
            phones = self.auth_use_case.get_available_phones()
            
            if not phones:
                LOGGER.error("No phone numbers available for OTP")
                return self.async_show_form(
                    step_id="phone_selection",
                    data_schema=vol.Schema({}),
                    errors={"base": "no_phones_available"}
                )
            
            # Create phone options for the form
            phone_options = {
                str(phone.get("id")): f"{phone.get('phone', 'Unknown')} (ID: {phone.get('id')})"
                for phone in phones
            }
        except Exception as e:
            LOGGER.error("Error getting available phones: %s", e)
            return self.async_show_form(
                step_id="phone_selection",
                data_schema=vol.Schema({}),
                errors={"base": "phone_retrieval_failed"}
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
            
            try:
                # Verify OTP
                if await self.auth_use_case.verify_otp(otp_code):
                    # Small delay to ensure SessionManager is fully updated
                    import asyncio
                    await asyncio.sleep(0.1)
                    return await self.async_step_installation()
                else:
                    errors["base"] = "invalid_otp"
            except MyVerisureOTPError:
                errors["base"] = "invalid_otp"
            except Exception as e:
                LOGGER.error("Error in OTP verification: %s", e)
                errors["base"] = "unknown"
            # Don't clear dependencies here - they're needed for the next step

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
        """Handle installation selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            installation_id = user_input[CONF_INSTALLATION_ID]
            
            # Check SessionManager state before getting installations
            session_manager = get_session_manager()
            LOGGER.warning("SessionManager state before getting installations:")
            LOGGER.warning("  - SessionManager instance ID: %s", id(session_manager))
            LOGGER.warning("  - Is authenticated: %s", session_manager.is_authenticated)
            LOGGER.warning("  - Has hash token: %s", bool(session_manager.get_current_hash_token()))
            LOGGER.warning("  - Username: %s", session_manager.username)
            LOGGER.warning("  - Hash token (first 50 chars): %s", session_manager.get_current_hash_token()[:50] + "..." if session_manager.get_current_hash_token() else "None")
            
            self.installation_use_case = get_installation_use_case()

            
            try:
                # Verify the installation exists and is accessible
                installations = await self.installation_use_case.get_installations()
                installation = next(
                    (inst for inst in installations if inst.numinst == installation_id),
                    None
                )
                
                if installation:
                    create_dummy_camera_images_use_case = get_create_dummy_camera_images_use_case()
                    await create_dummy_camera_images_use_case.create_dummy_camera_images(
                        installation_id=installation_id,
                    )
                    # Create the config entry
                    return self.async_create_entry(
                        title=f"My Verisure - {installation.alias or installation_id}",
                        data={
                            CONF_USER: self.user,
                            CONF_PASSWORD: self.password,
                            CONF_INSTALLATION_ID: installation_id,
                            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        },
                    )
                else:
                    errors["base"] = "installation_not_found"
            except Exception as e:
                LOGGER.error("Error in installation selection: %s", e)
                errors["base"] = "unknown"
            # Don't clear dependencies here - they're needed for the next step

        installations = await self.installation_use_case.get_installations()
        
        # Create installation options for the form
        installation_options = {
            inst.numinst: f"{inst.alias or inst.numinst} ({inst.type})"
            for inst in installations
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

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.user = user_input[CONF_USER]
            self.password = user_input[CONF_PASSWORD]
            
            # Dependencies should already be set up from previous step
            if not hasattr(self, 'auth_use_case') or self.auth_use_case is None:
                setup_dependencies()
                self.auth_use_case = get_auth_use_case()
            
            try:
                # Perform login using auth use case
                auth_result = await self.auth_use_case.login(self.user, self.password)
                
                if auth_result.success:
                    # Update the config entry
                    existing_entry = self.hass.config_entries.async_get_entry(
                        self.context["entry_id"]
                    )
                    if existing_entry:
                        self.hass.config_entries.async_update_entry(
                            existing_entry,
                            data={
                                **existing_entry.data,
                                CONF_USER: self.user,
                                CONF_PASSWORD: self.password,
                            },
                        )
                        await self.hass.config_entries.async_reload(
                            existing_entry.entry_id
                        )
                        return self.async_abort(reason="reauth_successful")
                else:
                    errors["base"] = "invalid_auth"
                    
            except MyVerisureAuthenticationError:
                errors["base"] = "invalid_auth"
            except MyVerisureConnectionError:
                errors["base"] = "cannot_connect"
            except MyVerisureOTPError:
                # For reauth, we'll just show an error instead of handling OTP
                errors["base"] = "otp_required"
            except MyVerisureError as ex:
                LOGGER.warning("Unexpected error from My Verisure: %s", ex)
                errors["base"] = "unknown"
            # Don't clear dependencies here - they're needed for the next step

        return self.async_show_form(
            step_id="reauth",
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

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

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
                }
            ),
        )
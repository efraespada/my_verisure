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

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
)
from core.dependency_injection.providers import (
    setup_dependencies,
    get_auth_use_case,
    get_session_use_case,
    get_installation_use_case,
    clear_dependencies,
)
from .const import (
    CONF_INSTALLATION_ID,
    CONF_USER,
    CONF_PHONE_ID,
    CONF_OTP_CODE,
    DOMAIN,
    LOGGER,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)


class MyVerisureConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Verisure."""

    VERSION = 1

    user: str
    password: str
    auth_use_case: Any
    session_use_case: Any
    installation_use_case: Any

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
            
            # Setup dependencies
            setup_dependencies(username=self.user, password=self.password)
            
            # Get use cases
            self.auth_use_case = get_auth_use_case()
            self.session_use_case = get_session_use_case()
            self.installation_use_case = get_installation_use_case()

            try:
                # Perform login using auth use case
                auth_result = await self.auth_use_case.login(self.user, self.password)
                
                if auth_result.success:
                    return await self.async_step_installation()
                else:
                    errors["base"] = "invalid_auth"
                    
            except MyVerisureAuthenticationError:
                LOGGER.debug("Invalid credentials for My Verisure")
                errors["base"] = "invalid_auth"
            except MyVerisureConnectionError:
                LOGGER.debug("Connection error to My Verisure")
                errors["base"] = "cannot_connect"
            except MyVerisureOTPError:
                LOGGER.debug("OTP authentication required")
                # Check if we have phone numbers available
                phones = self.auth_use_case.get_available_phones()
                if phones:
                    return await self.async_step_phone_selection()
                else:
                    errors["base"] = "otp_required"
            except MyVerisureError as ex:
                LOGGER.debug("Unexpected error from My Verisure: %s", ex)
                errors["base"] = "unknown"
            finally:
                # Clean up dependencies
                clear_dependencies()

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
            phone_id = user_input[CONF_PHONE_ID]
            
            # Setup dependencies again
            setup_dependencies(username=self.user, password=self.password)
            self.auth_use_case = get_auth_use_case()
            
            try:
                # Select phone and send OTP
                if self.auth_use_case.select_phone(phone_id):
                    # Send OTP using the phone_id as record_id and the stored otp_hash
                    otp_hash = getattr(self.auth_use_case._otp_data, "otp_hash", None)
                    if otp_hash:
                        otp_sent = await self.auth_use_case.send_otp(phone_id, otp_hash)
                        if otp_sent:
                            return await self.async_step_otp_verification()
                        else:
                            errors["base"] = "otp_send_failed"
                    else:
                        errors["base"] = "otp_data_missing"
                else:
                    errors["base"] = "phone_selection_failed"
            except Exception as e:
                LOGGER.error("Error in phone selection: %s", e)
                errors["base"] = "unknown"
            finally:
                clear_dependencies()

        # Get available phones
        setup_dependencies(username=self.user, password=self.password)
        self.auth_use_case = get_auth_use_case()
        phones = self.auth_use_case.get_available_phones()
        
        # Create phone options for the form
        phone_options = {
            str(phone.get("id")): f"{phone.get('phone', 'Unknown')} (ID: {phone.get('id')})"
            for phone in phones
        }

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
            
            # Setup dependencies again
            setup_dependencies(username=self.user, password=self.password)
            self.auth_use_case = get_auth_use_case()
            self.installation_use_case = get_installation_use_case()
            
            try:
                # Verify OTP
                if await self.auth_use_case.verify_otp(otp_code):
                    return await self.async_step_installation()
                else:
                    errors["base"] = "invalid_otp"
            except MyVerisureOTPError:
                errors["base"] = "invalid_otp"
            except Exception as e:
                LOGGER.error("Error in OTP verification: %s", e)
                errors["base"] = "unknown"
            finally:
                clear_dependencies()

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
            
            # Setup dependencies again
            setup_dependencies(username=self.user, password=self.password)
            self.installation_use_case = get_installation_use_case()
            
            try:
                # Verify the installation exists and is accessible
                installations = await self.installation_use_case.get_installations()
                installation = next(
                    (inst for inst in installations if inst.numinst == installation_id),
                    None
                )
                
                if installation:
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
            finally:
                clear_dependencies()

        # Get available installations
        setup_dependencies(username=self.user, password=self.password)
        self.installation_use_case = get_installation_use_case()
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
            
            # Setup dependencies
            setup_dependencies(username=self.user, password=self.password)
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
                LOGGER.debug("Unexpected error from My Verisure: %s", ex)
                errors["base"] = "unknown"
            finally:
                clear_dependencies()

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
                        default=self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): int,
                }
            ),
        )
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

from core.api.client import MyVerisureClient
from core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
)
from .const import CONF_INSTALLATION_ID, CONF_USER, CONF_PHONE_ID, CONF_OTP_CODE, DOMAIN, LOGGER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL


class MyVerisureConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for My Verisure."""

    VERSION = 1

    user: str
    password: str
    client: MyVerisureClient

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
            self.client = MyVerisureClient(
                user=self.user,
                password=self.password,
            )

            try:
                await self.client.connect()
                await self.client.login()
            except MyVerisureAuthenticationError:
                LOGGER.debug("Invalid credentials for My Verisure")
                errors["base"] = "invalid_auth"
            except MyVerisureConnectionError:
                LOGGER.debug("Connection error to My Verisure")
                errors["base"] = "cannot_connect"
            except MyVerisureOTPError:
                LOGGER.debug("OTP authentication required")
                # Check if we have phone numbers available
                phones = self.client.get_available_phones()
                if phones:
                    return await self.async_step_phone_selection()
                else:
                    errors["base"] = "otp_required"
            except MyVerisureError as ex:
                LOGGER.debug("Unexpected error from My Verisure: %s", ex)
                errors["base"] = "unknown"
            else:
                return await self.async_step_installation()

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
        """Handle phone number selection for OTP."""
        errors: dict[str, str] = {}

        if user_input is not None:
            phone_id = user_input[CONF_PHONE_ID]
            
            try:
                # Select the phone and send OTP
                phone_id_int = int(phone_id)
                LOGGER.debug("Selected phone ID: %s (int: %d)", phone_id, phone_id_int)
                
                if self.client.select_phone(phone_id_int):
                    LOGGER.debug("Phone selected successfully, sending OTP...")
                    await self.client.send_otp(phone_id_int, self.client._otp_data["otp_hash"])
                    LOGGER.debug("OTP sent successfully")
                    return await self.async_step_otp_verification()
                else:
                    LOGGER.error("Failed to select phone ID: %d", phone_id_int)
                    errors["base"] = "otp_failed"
            except MyVerisureOTPError as ex:
                LOGGER.error("Failed to send OTP: %s", ex)
                errors["base"] = "otp_failed"
            except Exception as ex:
                LOGGER.error("Unexpected error sending OTP: %s", ex)
                import traceback
                LOGGER.error("Traceback: %s", traceback.format_exc())
                errors["base"] = "unknown"

        # Get available phone numbers
        phones = self.client.get_available_phones()
        phone_options = {
            str(phone["id"]): f"{phone['phone']}"
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
            
            try:
                # Verify the OTP
                LOGGER.debug("Verifying OTP code: %s", otp_code)
                if await self.client.verify_otp(otp_code):
                    LOGGER.warning("OTP verification successful")
                    LOGGER.warning("Client token after OTP verification: %s", 
                               self.client._hash[:50] + "..." if self.client._hash else "None")
                    
                    # Ensure client is still connected and authenticated
                    if not self.client._hash:
                        LOGGER.error("Client lost authentication token after OTP verification")
                        errors["base"] = "otp_failed"
                        return self.async_show_form(
                            step_id="otp_verification",
                            data_schema=vol.Schema(
                                {
                                    vol.Required(CONF_OTP_CODE): str,
                                }
                            ),
                            errors=errors,
                        )
                    
                    # Ensure session data is available
                    if not self.client._session_data:
                        LOGGER.error("Client lost session data after OTP verification")
                        errors["base"] = "otp_failed"
                        return self.async_show_form(
                            step_id="otp_verification",
                            data_schema=vol.Schema(
                                {
                                    vol.Required(CONF_OTP_CODE): str,
                                }
                            ),
                            errors=errors,
                        )
                    
                    LOGGER.warning("Client authentication confirmed, proceeding to installation selection")
                    LOGGER.warning("Client state - Token: %s, Session: %s, Cookies: %s", 
                               "Present" if self.client._hash else "None",
                               "Active" if self.client._session else "None",
                               len(self.client._cookies) if self.client._cookies else 0)
                    return await self.async_step_installation()
                else:
                    LOGGER.error("OTP verification returned False")
                    errors["base"] = "otp_invalid"
            except MyVerisureOTPError as ex:
                LOGGER.error("Invalid OTP: %s", ex)
                errors["base"] = "otp_invalid"
            except MyVerisureDeviceAuthorizationError as ex:
                LOGGER.error("Device authorization failed: %s", ex)
                errors["base"] = "device_not_authorized"
            except Exception as ex:
                LOGGER.error("Unexpected error verifying OTP: %s", ex)
                import traceback
                LOGGER.error("Traceback: %s", traceback.format_exc())
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
        """Select My Verisure installation to add."""
        try:
            # Verify client is still authenticated
            if not self.client._hash:
                LOGGER.error("Client not authenticated when trying to get installations")
                return self.async_abort(reason="not_authenticated")
            
            LOGGER.warning("Client authenticated, getting installations...")
            
            # Ensure client session is still active
            if not self.client._session:
                LOGGER.warning("Client session lost, reconnecting...")
                await self.client.connect()
            
            installations_data = await self.client.get_installations()
            LOGGER.warning("Installations data received: %s", installations_data)
            
            installations = {}
            for inst in installations_data:
                LOGGER.warning("Processing installation: %s", inst)
                
                installation_id = inst.get("numinst")
                installation_name = inst.get("alias", "Unknown")
                address = inst.get("address", {})
                
                LOGGER.warning("Installation %s: id=%s, name=%s, address=%s (type: %s)", 
                           installation_id, installation_id, installation_name, address, type(address))
                
                # Handle case where address might be a string or dict
                if isinstance(address, dict):
                    street = address.get("street", "Unknown address")
                else:
                    # If address is a string, use it directly
                    street = str(address) if address else "Unknown address"
                
                if installation_id:
                    installations[installation_id] = f"{installation_name} ({street})"

            if user_input is None:
                if len(installations) != 1:
                    return self.async_show_form(
                        step_id="installation",
                        data_schema=vol.Schema(
                            {vol.Required(CONF_INSTALLATION_ID): vol.In(installations)}
                        ),
                    )
                user_input = {CONF_INSTALLATION_ID: list(installations)[0]}

            await self.async_set_unique_id(user_input[CONF_INSTALLATION_ID])
            self._abort_if_unique_id_configured()

            # Save session before creating the config entry
            try:
                from homeassistant.helpers.storage import STORAGE_DIR
                session_file = self.hass.config.path(
                    STORAGE_DIR, f"my_verisure_{self.user}.json"
                )
                await self.client.save_session(session_file)
                LOGGER.warning("Session saved successfully before creating config entry")
            except Exception as e:
                LOGGER.error("Failed to save session: %s", e)

            config_data = {
                CONF_USER: self.user,
                CONF_PASSWORD: self.password,
                CONF_INSTALLATION_ID: user_input[CONF_INSTALLATION_ID],
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
            }
            LOGGER.warning("Creating config entry with data: %s", config_data)
            return self.async_create_entry(
                title=installations[user_input[CONF_INSTALLATION_ID]],
                data=config_data,
            )
        except MyVerisureError as ex:
            LOGGER.error("Failed to get installations: %s", ex)
            return self.async_abort(reason="cannot_get_installations")
        except Exception as ex:
            LOGGER.error("Unexpected error getting installations: %s", ex)
            import traceback
            LOGGER.error("Traceback: %s", traceback.format_exc())
            return self.async_abort(reason="cannot_get_installations")

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle initiation of re-authentication with My Verisure."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle re-authentication with My Verisure."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.user = user_input[CONF_USER]
            self.password = user_input[CONF_PASSWORD]

            self.client = MyVerisureClient(
                user=self.user,
                password=self.password,
            )

            try:
                await self.client.connect()
                await self.client.login()
            except MyVerisureAuthenticationError:
                LOGGER.debug("Invalid credentials for My Verisure")
                errors["base"] = "invalid_auth"
            except MyVerisureConnectionError:
                LOGGER.debug("Connection error to My Verisure")
                errors["base"] = "cannot_connect"
            except MyVerisureError as ex:
                LOGGER.debug("Unexpected error from My Verisure: %s", ex)
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={
                        CONF_USER: user_input[CONF_USER],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_SCAN_INTERVAL: self._get_reauth_entry().data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USER, default=self._get_reauth_entry().data[CONF_USER]
                    ): str,
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
        """Manage My Verisure options."""
        if user_input is not None:
            LOGGER.warning("Saving options: %s", user_input)
            return self.async_create_entry(data=user_input)

        current_value = self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        LOGGER.warning("Current scan_interval value: %s (type: %s), default: %s (type: %s)", 
                      current_value, type(current_value), DEFAULT_SCAN_INTERVAL, type(DEFAULT_SCAN_INTERVAL))
        
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=current_value
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=9, max=60)
                ),
            }),
        ) 
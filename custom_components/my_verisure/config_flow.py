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

from .api import MyVerisureClient
from .api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
)
from .const import CONF_INSTALLATION_ID, CONF_USER, CONF_PHONE_ID, CONF_OTP_CODE, DOMAIN, LOGGER


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
                if self.client.select_phone(phone_id):
                    await self.client.send_otp(phone_id, self.client._otp_data["otp_hash"])
                    return await self.async_step_otp_verification()
                else:
                    errors["base"] = "otp_failed"
            except MyVerisureOTPError as ex:
                LOGGER.debug("Failed to send OTP: %s", ex)
                errors["base"] = "otp_failed"
            except Exception as ex:
                LOGGER.debug("Unexpected error sending OTP: %s", ex)
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
                if await self.client.verify_otp(otp_code):
                    return await self.async_step_installation()
                else:
                    errors["base"] = "otp_invalid"
            except MyVerisureOTPError as ex:
                LOGGER.debug("Invalid OTP: %s", ex)
                errors["base"] = "otp_invalid"
            except Exception as ex:
                LOGGER.debug("Unexpected error verifying OTP: %s", ex)
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
            installations_data = await self.client.get_installations()
            installations = {
                inst["id"]: f"{inst['name']} ({inst['address']['street']})"
                for inst in installations_data
            }

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

            return self.async_create_entry(
                title=installations[user_input[CONF_INSTALLATION_ID]],
                data={
                    CONF_USER: self.user,
                    CONF_PASSWORD: self.password,
                    CONF_INSTALLATION_ID: user_input[CONF_INSTALLATION_ID],
                },
            )
        except MyVerisureError as ex:
            LOGGER.error("Failed to get installations: %s", ex)
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
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
        ) 
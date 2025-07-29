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
)
from .const import CONF_INSTALLATION_ID, CONF_USER, DOMAIN, LOGGER


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
            
            # Store credentials and proceed to installation step
            # We'll validate them later when getting installations
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

    async def async_step_installation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select My Verisure installation to add."""
        errors: dict[str, str] = {}
        
        # Create client and validate credentials
        if not hasattr(self, 'client') or self.client is None:
            self.client = MyVerisureClient(
                user=self.user,
                password=self.password,
            )
            
            try:
                await self.client.connect()
                await self.client.login()
            except MyVerisureAuthenticationError:
                LOGGER.debug("Invalid credentials for My Verisure")
                return self.async_abort(reason="invalid_auth")
            except MyVerisureConnectionError:
                LOGGER.debug("Connection error to My Verisure")
                return self.async_abort(reason="cannot_connect")
            except MyVerisureError as ex:
                LOGGER.debug("Unexpected error from My Verisure: %s", ex)
                return self.async_abort(reason="unknown")
        
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
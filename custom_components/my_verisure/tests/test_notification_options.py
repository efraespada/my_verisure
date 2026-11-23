"""Notification options defaults, dependencies and recoverable validation.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.my_verisure.core.const import (
    CONF_ADVANCED_EVENT_BUS,
    CONF_EXTERNAL_PHOTO_UPDATES,
    CONF_NOTIFICATION_OBSERVATION,
    CONF_PUSH_ENABLED,
    CONF_PUSH_STATE_REFRESH,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)


def entry(options=None):
    return MockConfigEntry(
        domain=DOMAIN,
        title="Synthetic home",
        data={"installation_id": "synthetic-home", CONF_SCAN_INTERVAL: 15},
        options=options or {},
    )


@pytest.mark.homeassistant
async def test_notification_defaults_are_conservative(hass, enable_custom_integrations):
    config_entry = entry()
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    defaults = result["data_schema"]({})
    assert defaults[CONF_NOTIFICATION_OBSERVATION] is True
    assert defaults[CONF_PUSH_ENABLED] is False
    assert defaults[CONF_PUSH_STATE_REFRESH] is False
    assert defaults[CONF_EXTERNAL_PHOTO_UPDATES] is False
    assert defaults[CONF_ADVANCED_EVENT_BUS] is False
    assert defaults[CONF_SCAN_INTERVAL] == 15


@pytest.mark.homeassistant
@pytest.mark.parametrize(
    "values",
    [
        {CONF_PUSH_STATE_REFRESH: True, CONF_PUSH_ENABLED: False},
        {CONF_EXTERNAL_PHOTO_UPDATES: True, CONF_PUSH_ENABLED: False},
        {CONF_ADVANCED_EVENT_BUS: True, CONF_NOTIFICATION_OBSERVATION: False},
    ],
)
async def test_invalid_dependencies_keep_reviewable_form(
    hass,
    enable_custom_integrations,
    values,
):
    config_entry = entry()
    config_entry.add_to_hass(hass)
    start = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(start["flow_id"], values)
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_options"}
    defaults = result["data_schema"]({})
    assert all(defaults[key] == value for key, value in values.items())
    assert config_entry.options == {}


@pytest.mark.homeassistant
@pytest.mark.parametrize(
    "values",
    [
        {
            CONF_PUSH_ENABLED: True,
            CONF_NOTIFICATION_OBSERVATION: True,
            CONF_PUSH_STATE_REFRESH: True,
            CONF_EXTERNAL_PHOTO_UPDATES: True,
            CONF_ADVANCED_EVENT_BUS: True,
        },
        {
            CONF_PUSH_ENABLED: True,
            CONF_NOTIFICATION_OBSERVATION: False,
            CONF_PUSH_STATE_REFRESH: True,
            CONF_EXTERNAL_PHOTO_UPDATES: True,
            CONF_ADVANCED_EVENT_BUS: False,
        },
        {
            CONF_PUSH_ENABLED: False,
            CONF_NOTIFICATION_OBSERVATION: True,
            CONF_ADVANCED_EVENT_BUS: True,
        },
    ],
)
async def test_supported_options_are_preserved(
    hass,
    enable_custom_integrations,
    values,
):
    config_entry = entry()
    config_entry.add_to_hass(hass)
    start = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(start["flow_id"], values)
    assert result["type"] == "create_entry"
    assert all(result["data"][key] == value for key, value in values.items())


@pytest.mark.homeassistant
async def test_disabling_push_does_not_silently_keep_dependent_refresh(
    hass,
    enable_custom_integrations,
):
    config_entry = entry({CONF_PUSH_ENABLED: True, CONF_PUSH_STATE_REFRESH: True})
    config_entry.add_to_hass(hass)
    start = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        start["flow_id"],
        {CONF_PUSH_ENABLED: False},
    )
    assert result["errors"] == {"base": "invalid_options"}
    corrected = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {CONF_PUSH_ENABLED: False, CONF_PUSH_STATE_REFRESH: False},
    )
    assert corrected["type"] == "create_entry"
    assert corrected["data"][CONF_PUSH_ENABLED] is False
    assert corrected["data"][CONF_PUSH_STATE_REFRESH] is False

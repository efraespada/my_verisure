"""Home Assistant options flow coverage."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.core.const import (
    CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL,
    CONF_DEV_MODE,
    CONF_INSTALLATION_ID,
    CONF_SCAN_INTERVAL,
    CONF_USER,
    DOMAIN,
)


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_options_flow_persists_scan_and_runtime_options(
    hass, enable_custom_integrations
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing",
        data={
            CONF_INSTALLATION_ID: "home-1",
            CONF_USER: "user@example.invalid",
            "password": "[REDACTED]",
            CONF_SCAN_INTERVAL: 15,
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_SCAN_INTERVAL: 5,
            CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL: True,
            CONF_DEV_MODE: True,
        },
    )

    assert result["type"] == "create_entry"
    assert result["data"] == {
        CONF_SCAN_INTERVAL: 5,
        CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL: True,
        CONF_DEV_MODE: True,
    }

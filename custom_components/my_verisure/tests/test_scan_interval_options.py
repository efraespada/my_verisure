"""Protect provider polling against malformed and too-frequent intervals.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import pytest
import probatio
from homeassistant.data_entry_flow import InvalidData
from homeassistant.helpers import config_validation as cv
from pytest_homeassistant.common import MockConfigEntry

from custom_components.my_verisure.config_flow import MyVerisureOptionsFlowHandler
from custom_components.my_verisure.core.const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


@pytest.mark.homeassistant
async def test_options_schema_serializes_for_frontend_and_recovers_invalid_input(
    hass, enable_custom_integrations
):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    start = await hass.config_entries.options.async_init(entry.entry_id)

    def serialized_interval(form):
        fields = probatio.to_field_list(
            form["data_schema"], custom_serializer=cv.custom_serializer
        )
        return next(field for field in fields if field["name"] == CONF_SCAN_INTERVAL)

    field = serialized_interval(start)
    assert field["type"] == "integer"
    assert field["valueMin"] == 1
    assert field["valueMax"] == 1440
    assert field["default"] == DEFAULT_SCAN_INTERVAL

    result = await hass.config_entries.options.async_configure(
        start["flow_id"], {CONF_SCAN_INTERVAL: True}
    )
    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_options"}
    assert entry.options == {}
    assert serialized_interval(result) == field


@pytest.mark.homeassistant
@pytest.mark.parametrize("interval", [-1, 0, True, False, "1", 1.5, 10**100])
async def test_options_reject_unsafe_polling_interval(
    hass, enable_custom_integrations, interval
):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    start = await hass.config_entries.options.async_init(entry.entry_id)
    if interval is True:
        # Python's standard int validator admits True. The domain policy must
        # still reject it in the actual flow, before anything is persisted.
        rejected = await hass.config_entries.options.async_configure(
            start["flow_id"], {CONF_SCAN_INTERVAL: interval}
        )
        assert rejected["type"] == "form"
        assert rejected["errors"] == {"base": "invalid_options"}
    else:
        with pytest.raises(probatio.Invalid):
            start["data_schema"]({CONF_SCAN_INTERVAL: interval})
        with pytest.raises(InvalidData):
            await hass.config_entries.options.async_configure(
                start["flow_id"], {CONF_SCAN_INTERVAL: interval}
            )

    handler = MyVerisureOptionsFlowHandler()
    handler.hass = hass
    handler.handler = entry.entry_id
    result = await handler.async_step_init({CONF_SCAN_INTERVAL: interval})

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_options"}
    assert entry.options == {}
    assert result["data_schema"]({})[CONF_SCAN_INTERVAL] == DEFAULT_SCAN_INTERVAL


@pytest.mark.homeassistant
@pytest.mark.parametrize("interval", [1, 10, 1440])
async def test_options_accept_safe_integer_minutes(
    hass, enable_custom_integrations, interval
):
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    start = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        start["flow_id"], {CONF_SCAN_INTERVAL: interval}
    )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_SCAN_INTERVAL] == interval

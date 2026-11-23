"""Defend the polling fallback for already persisted entry options.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from datetime import timedelta
from functools import partial

import pytest
from pytest_homeassistant.common import MockConfigEntry

from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.const import DEFAULT_SCAN_INTERVAL


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [-1, 0, True, False, "1", 1.5, 1441, 10**100])
async def test_invalid_stored_polling_interval_uses_safe_default(hass, value):
    entry = MockConfigEntry(
        domain="my_verisure",
        data={"installation_id": "synthetic-home"},
        options={"scan_interval": value},
    )
    coordinator = await hass.async_add_executor_job(
        partial(MyVerisureDataUpdateCoordinator, hass, entry)
    )
    try:
        assert coordinator.update_interval == timedelta(minutes=DEFAULT_SCAN_INTERVAL)
    finally:
        await coordinator.async_cleanup()


@pytest.mark.asyncio
@pytest.mark.parametrize("value", [1, 1440])
async def test_valid_stored_polling_interval_is_preserved(hass, value):
    entry = MockConfigEntry(
        domain="my_verisure",
        data={"installation_id": "synthetic-home"},
        options={"scan_interval": value},
    )
    coordinator = await hass.async_add_executor_job(
        partial(MyVerisureDataUpdateCoordinator, hass, entry)
    )
    try:
        assert coordinator.update_interval == timedelta(minutes=value)
    finally:
        await coordinator.async_cleanup()

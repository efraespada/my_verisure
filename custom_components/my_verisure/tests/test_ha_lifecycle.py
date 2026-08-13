"""Real Home Assistant lifecycle tests for the My Verisure integration."""

from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.core.const import DOMAIN


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_starts_with_user_form(hass, enable_custom_integrations):
    """The real HA config-entry manager exposes the initial user form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": "user"},
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_entry_setup_and_unload_are_isolated(
    hass, enable_custom_integrations
):
    """A config entry can be set up and unloaded through HA's real manager."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Test My Verisure",
        data={
            "installation_id": "123",
            "user": "test@example.invalid",
            "password": "not-a-real-password",
        },
    )
    entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_load_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.get_session_hash",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.load_alarm_info",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.has_valid_session",
            return_value=False,
        ),
        patch(
            "custom_components.my_verisure.device.async_setup_device",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(return_value=None),
        ),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        assert entry.state.name == "LOADED"
        assert entry.runtime_data is not None
        assert DOMAIN in hass.data
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert entry.state.name == "NOT_LOADED"
        assert DOMAIN not in hass.data


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_two_config_entries_keep_runtime_data_separate(
    hass, enable_custom_integrations
):
    """Two HA entries receive distinct coordinators and composition roots."""
    entries = [
        MockConfigEntry(
            domain=DOMAIN,
            title=f"Test My Verisure {index}",
            entry_id=f"entry-{index}",
            data={
                "installation_id": str(index),
                "user": f"test-{index}@example.invalid",
                "password": "not-a-real-password",
            },
        )
        for index in (1, 2)
    ]
    for entry in entries:
        entry.add_to_hass(hass)

    with (
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_load_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.get_session_hash",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.load_alarm_info",
            return_value=None,
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.has_valid_session",
            return_value=False,
        ),
        patch(
            "custom_components.my_verisure.device.async_setup_device",
            new=AsyncMock(return_value=None),
        ),
        patch.object(
            hass.config_entries,
            "async_forward_entry_setups",
            new=AsyncMock(return_value=None),
        ),
    ):
        assert await hass.config_entries.async_setup(entries[0].entry_id)
        assert entries[0].state.name == "LOADED"
        assert entries[1].state.name == "LOADED"
        assert entries[0].runtime_data is not entries[1].runtime_data
        assert (
            entries[0].runtime_data.composition_root
            is not entries[1].runtime_data.composition_root
        )
        assert entries[0].runtime_data.installation_id == "1"
        assert entries[1].runtime_data.installation_id == "2"

        assert await hass.config_entries.async_unload(entries[0].entry_id)
        assert entries[1].state.name == "LOADED"
        assert await hass.config_entries.async_unload(entries[1].entry_id)

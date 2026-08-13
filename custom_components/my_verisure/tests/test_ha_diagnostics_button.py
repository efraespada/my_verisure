"""Focused tests for diagnostics and camera refresh button lifecycle."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.button import RefreshCameraImagesButton
from custom_components.my_verisure.core.const import DOMAIN
from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.diagnostics import async_get_config_entry_diagnostics


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test",
        entry_id="entry-1",
        data={
            "installation_id": "home-1",
            "user": "user@example.invalid",
            "password": "[REDACTED]",
        },
    )


@pytest.mark.asyncio
async def test_diagnostics_redacts_credentials_and_returns_safe_summary() -> None:
    entry = _entry()
    coordinator = SimpleNamespace(
        data={
            "installation_id": "home-1",
            "alarm_status": {},
            "detailed_installation": {},
            "last_updated": 123.0,
        },
        session_manager=SimpleNamespace(
            is_authenticated=True,
            is_session_valid=lambda: True,
        ),
        last_update_success=True,
        update_interval=SimpleNamespace(total_seconds=lambda: 300.0),
    )
    entry.runtime_data = coordinator

    result = await async_get_config_entry_diagnostics(MagicMock(), entry)

    assert result["entry"]["data"]["user"] == "**REDACTED**"
    assert result["entry"]["data"]["password"] == "**REDACTED**"
    assert result["coordinator"]["data_summary"]["has_alarm_status"] is True
    assert result["coordinator"]["session"] == {
        "is_authenticated": True,
        "session_valid": True,
    }


@pytest.mark.asyncio
async def test_button_clears_executing_state_after_success() -> None:
    hass = SimpleNamespace(
        services=SimpleNamespace(async_call=AsyncMock()),
    )
    coordinator = MagicMock(spec=MyVerisureDataUpdateCoordinator)
    coordinator.last_update_success = True
    button = RefreshCameraImagesButton(coordinator, "home-1", _entry())
    button.hass = hass
    button.async_write_ha_state = MagicMock()

    await button.async_press()

    assert button.extra_state_attributes["is_executing"] is False
    hass.services.async_call.assert_awaited_once_with(
        DOMAIN,
        "refresh_camera_images",
        {"installation_id": "home-1"},
    )


@pytest.mark.asyncio
async def test_button_clears_executing_state_after_failure() -> None:
    hass = SimpleNamespace(
        services=SimpleNamespace(
            async_call=AsyncMock(side_effect=RuntimeError("service failed"))
        ),
    )
    coordinator = MagicMock(spec=MyVerisureDataUpdateCoordinator)
    coordinator.last_update_success = True
    button = RefreshCameraImagesButton(coordinator, "home-1", _entry())
    button.hass = hass
    button.async_write_ha_state = MagicMock()

    await button.async_press()

    assert button.extra_state_attributes["is_executing"] is False
    assert button.available is True

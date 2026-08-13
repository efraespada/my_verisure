"""Additional real config-entry authentication lifecycle coverage."""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.core.const import DOMAIN
from custom_components.my_verisure.core.api.models.domain.auth import AuthResult
from custom_components.my_verisure.tests.test_ha_lifecycle import _FakeAuthUseCase, _FakeRoot


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_setup_auth_failure_starts_real_reauth_flow(
    hass, enable_custom_integrations
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Auth failure",
        data={
            "installation_id": "home-1",
            "user": "user@example.invalid",
            "password": "[REDACTED]",
        },
    )
    entry.add_to_hass(hass)
    root = _FakeRoot(_FakeAuthUseCase(AuthResult(False, "invalid")), [])

    with (
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_load_session",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "custom_components.my_verisure.coordinator.MyVerisureDataUpdateCoordinator.async_config_entry_first_refresh",
            new=AsyncMock(side_effect=ConfigEntryAuthFailed),
        ),
        patch(
            "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
            return_value=root,
        ),
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)

    assert entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["context"]["entry_id"] == entry.entry_id

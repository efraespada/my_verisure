"""Additional Home Assistant config-flow branch coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureConnectionError,
    MyVerisureOTPError,
    MyVerisurePersistenceError,
)
from custom_components.my_verisure.core.application.models.auth import AuthResult
from custom_components.my_verisure.core.const import DOMAIN
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.use_cases.interfaces.auth_use_case import AuthUseCase
from custom_components.my_verisure.core.use_cases.interfaces.installation_use_case import InstallationUseCase
from custom_components.my_verisure.tests.test_ha_lifecycle import _FakeAuthUseCase, _FakeRoot


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_routes_otp_to_phone_selection(hass, enable_custom_integrations):
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    root.values[AuthUseCase].get_available_phones = lambda: [
        {
            "id": 1,
            "phone": "[REDACTED]",
            "record_id": 1,
            "otp_hash": "[REDACTED]",
        }
    ]
    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "phone_selection"




@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_rejects_non_positive_otp_record_id(
    hass, enable_custom_integrations
):
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = lambda: [
        {"id": 1, "phone": "[REDACTED]", "record_id": 0}
    ]
    auth.select_phone = Mock(return_value=True)
    auth.send_otp = AsyncMock(return_value=True)

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"phone_id": "1"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "phone_selection"
    auth.send_otp.assert_not_awaited()


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_reports_invalid_otp(
    hass, enable_custom_integrations
):
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = lambda: [
        {
            "id": 1,
            "phone": "[REDACTED]",
            "record_id": 1,
            "otp_hash": "[REDACTED]",
        }
    ]
    auth.select_phone = Mock(return_value=True)
    auth._otp_data = {"otp_hash": "[REDACTED]"}
    auth.send_otp = AsyncMock(return_value=True)
    auth.verify_otp = AsyncMock(side_effect=MyVerisureOTPError("invalid"))

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"phone_id": "1"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"otp_code": "123456"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "otp_verification"
    assert result["errors"] == {"base": "otp_invalid"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_initial_otp_persistence_failure_cleans_and_restarts_flow(
    hass, enable_custom_integrations
):
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = lambda: [
        {"id": 1, "phone": "[REDACTED]", "record_id": 1, "otp_hash": "[REDACTED]"}
    ]
    auth.select_phone = Mock(return_value=True)
    auth.send_otp = AsyncMock(return_value=True)
    auth.verify_otp = AsyncMock(
        side_effect=MyVerisurePersistenceError("persistence failed")
    )

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"user": "[REDACTED]", "password": "[REDACTED]"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"phone_id": "1"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"otp_code": "123456"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    root.values[FileManager].async_cleanup_project_root.assert_awaited_once()


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_invalid_login_result_stays_on_user_form(
    hass, enable_custom_integrations
):
    root = _FakeRoot(_FakeAuthUseCase(AuthResult(False, "invalid")), [])
    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_does_not_select_installation_without_otp_phone(
    hass, enable_custom_integrations
):
    """An empty OTP phone list must not bypass the OTP state machine."""
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = lambda: []
    root.values[InstallationUseCase].get_installations = AsyncMock(
        side_effect=AssertionError("installation lookup must not run before OTP")
    )

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "phone_selection"
    assert result["errors"] == {"base": "otp_no_phone_destinations"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_does_not_select_installation_when_otp_phone_lookup_fails(
    hass, enable_custom_integrations
):
    """A phone lookup failure must remain recoverable inside the OTP flow."""
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = Mock(
        side_effect=MyVerisureConnectionError("offline")
    )
    root.values[InstallationUseCase].get_installations = AsyncMock(
        side_effect=AssertionError("installation lookup must not run before OTP")
    )

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "phone_selection"
    assert result["errors"] == {"base": "cannot_connect"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_blocks_installation_without_authenticated_session(
    hass, enable_custom_integrations
):
    """Installation selection cannot create an entry without a valid session."""
    installation = type(
        "Installation",
        (),
        {"numinst": "123", "alias": "Home", "type": "alarm"},
    )()
    root = _FakeRoot(_FakeAuthUseCase(AuthResult(True, "ok")), [installation])
    root.values["session"].is_authenticated = False

    with patch(
        "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
        return_value=root,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": "user"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )
        assert result["step_id"] == "installation"
        assert result["errors"] == {"base": "authentication_required"}

    assert result["type"] == "form"
    assert result["step_id"] == "installation"
    assert result["errors"] == {"base": "authentication_required"}


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_reauth_otp_updates_entry_only_after_verification(
    hass, enable_custom_integrations
):
    """Re-authentication must complete OTP before changing the config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing My Verisure",
        data={
            "installation_id": "home-1",
            "user": "[REDACTED]",
            "password": "[REDACTED]",
        },
    )
    entry.add_to_hass(hass)

    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = lambda: [
        {
            "id": 7,
            "phone": "[REDACTED]",
            "record_id": 7,
            "otp_hash": "[REDACTED]",
        }
    ]
    auth.select_phone = Mock(return_value=True)
    auth.send_otp = AsyncMock(return_value=True)

    async def verify_otp(_otp_code):
        root.values["session"].is_authenticated = True
        return AuthResult(
            success=True,
            message="OTP verification successful",
            hash="[REDACTED]",
        )

    auth.verify_otp = AsyncMock(side_effect=verify_otp)

    with (
        patch(
            "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
            return_value=root,
        ),
        patch.object(
            hass.config_entries,
            "async_reload",
            new=AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth", "entry_id": entry.entry_id},
        )
        assert result["step_id"] == "reauth_confirm"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )
        assert result["step_id"] == "phone_selection"
        assert entry.data["user"] == "[REDACTED]"
        assert entry.data["password"] == "[REDACTED]"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"phone_id": "7"}
        )
        assert result["step_id"] == "otp_verification"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"otp_code": "123456"}
        )

    assert result["type"] == "abort"
    assert result["reason"] == "reauth_successful"
    assert entry.data["password"] == "[REDACTED]"


@pytest.mark.homeassistant
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("reload_results", "expected_type"),
    [([False, True], "form"), ([False, False], "abort")],
)
async def test_reauth_reload_failure_rolls_back_entry_data(
    hass, enable_custom_integrations, reload_results, expected_type
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing My Verisure",
        data={
            "installation_id": "home-1",
            "user": "[REDACTED]",
            "password": "[REDACTED]",
        },
    )
    entry.add_to_hass(hass)
    auth = _FakeAuthUseCase(
        result=AuthResult(success=True, message="authenticated", hash="[REDACTED]")
    )
    root = _FakeRoot(auth, [])
    root.values["session"].is_authenticated = True

    with (
        patch(
            "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
            return_value=root,
        ),
        patch.object(
            hass.config_entries,
            "async_reload",
            new=AsyncMock(side_effect=reload_results),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth", "entry_id": entry.entry_id},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == expected_type
    if expected_type == "form":
        assert result["errors"] == {"base": "cannot_persist"}
    else:
        assert result["reason"] == "cannot_persist"
    assert entry.data["user"] == "[REDACTED]"
    assert entry.data["password"] == "[REDACTED]"
    root.values["session"].async_restore_transaction_state.assert_awaited_once()
    root.values["session"].async_load_session_from_disk.assert_awaited_once()


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_reauth_failure_preserves_active_session_credentials(
    hass, enable_custom_integrations
):
    """Failed reauthentication must not overwrite the active session state."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing My Verisure",
        data={
            "installation_id": "home-1",
            "user": "[REDACTED]",
            "password": "[REDACTED]",
        },
    )
    entry.add_to_hass(hass)
    auth = _FakeAuthUseCase(error=MyVerisureConnectionError("transport failed"))
    root = _FakeRoot(auth, [])

    with (
        patch(
            "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
            return_value=root,
        ),
        patch.object(
            hass.config_entries, "async_reload", new=AsyncMock(return_value=True)
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth", "entry_id": entry.entry_id},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "cannot_connect"}
    assert entry.data["user"] == "[REDACTED]"
    assert entry.data["password"] == "[REDACTED]"
    assert root.values["session"].username == "[REDACTED]"
    root.values["session"].update_credentials.assert_not_called()


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_reauth_persistence_failure_maps_to_cannot_persist(
    hass, enable_custom_integrations
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Existing My Verisure",
        data={
            "installation_id": "home-1",
            "user": "[REDACTED]",
            "password": "[REDACTED]",
        },
    )
    entry.add_to_hass(hass)
    auth = _FakeAuthUseCase(error=MyVerisurePersistenceError("persistence failed"))
    root = _FakeRoot(auth, [])

    with (
        patch(
            "custom_components.my_verisure.config_flow.build_my_verisure_composition_root",
            return_value=root,
        ),
        patch.object(
            hass.config_entries, "async_reload", new=AsyncMock(return_value=True)
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": "reauth", "entry_id": entry.entry_id},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"user": "[REDACTED]", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "cannot_persist"}

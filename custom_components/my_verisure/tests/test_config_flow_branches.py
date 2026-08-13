"""Additional Home Assistant config-flow branch coverage."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.my_verisure.core.api.exceptions import MyVerisureOTPError
from custom_components.my_verisure.core.api.models.domain.auth import AuthResult
from custom_components.my_verisure.core.const import DOMAIN
from custom_components.my_verisure.core.use_cases.interfaces.auth_use_case import AuthUseCase
from custom_components.my_verisure.tests.test_ha_lifecycle import _FakeAuthUseCase, _FakeRoot


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_routes_otp_to_phone_selection(hass, enable_custom_integrations):
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    root.values[AuthUseCase].get_available_phones = lambda: [
        {"id": 1, "phone": "+346****0001"}
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
            {"user": "user@example.invalid", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "phone_selection"


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_config_flow_reports_invalid_otp(
    hass, enable_custom_integrations
):
    auth = _FakeAuthUseCase(error=MyVerisureOTPError("OTP required"))
    root = _FakeRoot(auth, [])
    auth.get_available_phones = lambda: [{"id": 1, "phone": "+346****0001"}]
    auth.select_phone = Mock(return_value=True)
    auth._otp_data = {"otp_hash": "otp-hash"}
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
            {"user": "user@example.invalid", "password": "[REDACTED]"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"phone_id": "1"}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"otp_code": "123456"}
        )

    assert result["type"] == "form"
    assert result["step_id"] == "otp_verification"
    assert result["errors"] == {"base": "invalid_otp"}


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
            {"user": "user@example.invalid", "password": "[REDACTED]"},
        )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

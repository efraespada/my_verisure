"""Pure interpretation of device-authorization GraphQL responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceAuthorizationSuccess:
    """The provider accepted the device authorization request."""

    data: dict[str, Any]


@dataclass(frozen=True)
class DeviceAuthorizationOTPChallenge:
    """The provider requires OTP-based device authorization."""

    data: dict[str, Any]


@dataclass(frozen=True)
class DeviceAuthorizationFailure:
    """The provider rejected device authorization."""

    message: str
    auth_code: str | None = None
    unauthorized: bool = False


DeviceAuthorizationDecision = (
    DeviceAuthorizationSuccess
    | DeviceAuthorizationOTPChallenge
    | DeviceAuthorizationFailure
)


def classify_device_authorization_response(
    result: object,
) -> DeviceAuthorizationDecision:
    """Classify a provider response without performing side effects.

    The normal GraphQL envelope is ``data.xSValidateDevice``.  The direct
    ``xSValidateDevice`` form is retained because older provider-shaped test
    fixtures and the previous client implementation accepted it.
    """
    if not isinstance(result, dict):
        return DeviceAuthorizationFailure("No response data")

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        if not isinstance(first_error, dict):
            return DeviceAuthorizationFailure("Device validation failed: Unknown error")

        error_data = first_error.get("data")
        if not isinstance(error_data, dict):
            error_data = {}
        auth_code = _as_optional_string(
            error_data.get("auth-code") or error_data.get("authCode")
        )
        auth_type = _as_optional_string(
            error_data.get("auth-type") or error_data.get("authType")
        )
        message = str(first_error.get("message", "Unknown error"))

        if auth_type == "OTP" or auth_code == "10001":
            return DeviceAuthorizationOTPChallenge(error_data)
        if auth_code == "10010":
            return DeviceAuthorizationFailure(
                "Device validation failed - unauthorized. This may require additional authentication steps.",
                auth_code=auth_code,
                unauthorized=True,
            )
        return DeviceAuthorizationFailure(
            f"Device validation failed: {message} (auth-code: {auth_code})",
            auth_code=auth_code,
        )

    device_data = _extract_device_data(result)
    if device_data is None:
        return DeviceAuthorizationFailure("No response data")
    if device_data.get("res") == "OK":
        return DeviceAuthorizationSuccess(device_data)
    return DeviceAuthorizationFailure(
        f"Device validation failed: {device_data.get('msg', 'Unknown error')}"
    )


def _extract_device_data(result: dict[str, Any]) -> dict[str, Any] | None:
    direct = result.get("xSValidateDevice")
    if isinstance(direct, dict):
        return direct
    wrapper = result.get("data")
    if isinstance(wrapper, dict):
        nested = wrapper.get("xSValidateDevice")
        if isinstance(nested, dict):
            return nested
    return None


def _as_optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None

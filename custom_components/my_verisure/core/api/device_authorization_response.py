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

    if "data" in result and not isinstance(result.get("data"), dict):
        return DeviceAuthorizationFailure("Device validation failed")

    if "errors" in result:
        errors = result["errors"]
        if not isinstance(errors, list) or len(errors) != 1:
            return DeviceAuthorizationFailure("Device validation failed")
        first_error = errors[0]
        if not isinstance(first_error, dict):
            return DeviceAuthorizationFailure("Device validation failed")

        error_data = first_error.get("data")
        if not isinstance(error_data, dict):
            error_data = {}
        auth_code, auth_code_conflict = _read_aliases(
            error_data, "auth-code", "authCode"
        )
        auth_type, auth_type_conflict = _read_aliases(
            error_data, "auth-type", "authType"
        )
        if auth_code_conflict or auth_type_conflict:
            return DeviceAuthorizationFailure("Device validation failed")

        if auth_type == "OTP" or auth_code == "10001":
            return DeviceAuthorizationOTPChallenge(error_data)
        if auth_code == "10010":
            return DeviceAuthorizationFailure(
                "Device validation failed - unauthorized. This may require additional authentication steps.",
                auth_code=auth_code,
                unauthorized=True,
            )
        return DeviceAuthorizationFailure(
            "Device validation failed",
            auth_code=auth_code,
        )

    device_data, ambiguous = _extract_device_data(result)
    if ambiguous:
        return DeviceAuthorizationFailure("Device validation failed")
    if device_data is None:
        return DeviceAuthorizationFailure("No response data")
    if device_data.get("res") == "OK":
        return DeviceAuthorizationSuccess(device_data)
    return DeviceAuthorizationFailure("Device validation failed")


def _extract_device_data(
    result: dict[str, Any],
) -> tuple[dict[str, Any] | None, bool]:
    direct_present = "xSValidateDevice" in result
    wrapper = result.get("data")
    nested_present = isinstance(wrapper, dict) and "xSValidateDevice" in wrapper
    direct = result.get("xSValidateDevice")
    nested = wrapper.get("xSValidateDevice") if nested_present and isinstance(wrapper, dict) else None
    if direct_present and nested_present:
        return None, True
    if direct_present:
        return direct if isinstance(direct, dict) else None, False
    if nested_present:
        return nested if isinstance(nested, dict) else None, False
    return None, False


def _read_aliases(
    data: dict[str, Any], first: str, second: str
) -> tuple[str | None, bool]:
    """Read equivalent fields and reject conflicting values."""
    values = [_as_optional_string(data[key]) for key in (first, second) if key in data]
    if len(values) == 2 and values[0] != values[1]:
        return None, True
    return (values[0] if values else None), False


def _as_optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None

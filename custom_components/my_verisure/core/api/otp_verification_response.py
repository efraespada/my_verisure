"""Pure interpretation of OTP verification responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OTPVerificationSuccess:
    """The OTP was accepted and the provider returned session data."""

    data: dict[str, Any]


@dataclass(frozen=True)
class OTPVerificationFailure:
    """The provider rejected the OTP verification request."""

    message: str
    retryable: bool = False
    code: str = "terminal"


OTPVerificationDecision = OTPVerificationSuccess | OTPVerificationFailure


def _is_invalid_code_message(message: object) -> bool:
    if not isinstance(message, str):
        return False
    return " ".join(message.lower().split()) in {
        "invalid code",
        "incorrect code",
        "wrong code",
    }


def _failure(message: str, provider_code: object = None) -> OTPVerificationFailure:
    normalized_code = (
        str(provider_code).strip().upper() if isinstance(provider_code, str) else ""
    )
    retryable = normalized_code in {"INVALID_CODE", "INVALID_OTP", "OTP_INVALID"} or message == "OTP verification failed: invalid code"
    return OTPVerificationFailure(
        "OTP verification failed: invalid code" if retryable else "OTP verification failed",
        retryable=retryable,
        code="invalid_code" if retryable else "terminal",
    )


def classify_otp_verification_response(
    result: object,
) -> OTPVerificationDecision:
    """Classify an OTP verification response without side effects."""
    if not isinstance(result, dict):
        return _failure("OTP verification failed: No response data")

    if "errors" in result:
        errors = result["errors"]
        if not isinstance(errors, list) or len(errors) != 1:
            return _failure("OTP verification failed")
        first_error = errors[0]
        if isinstance(first_error, dict):
            provider_message = first_error.get("message")
            extensions = first_error.get("extensions")
            provider_code = (
                extensions.get("code")
                if isinstance(extensions, dict)
                else None
            )
        else:
            provider_message = None
            provider_code = None
        return _failure(
            "OTP verification failed: invalid code"
            if _is_invalid_code_message(provider_message)
            else "OTP verification failed",
            provider_code,
        )

    wrapper_present = "data" in result
    wrapper = result.get("data")
    if wrapper_present and not isinstance(wrapper, dict):
        return _failure("OTP verification failed")
    direct_present = "xSValidateDevice" in result
    nested_present = isinstance(wrapper, dict) and "xSValidateDevice" in wrapper
    nested_data = wrapper.get("xSValidateDevice") if isinstance(wrapper, dict) else None
    if direct_present and nested_present:
        return _failure("ambiguous OTP response envelope")
    if direct_present and not isinstance(result["xSValidateDevice"], dict):
        return _failure("OTP verification failed")
    if nested_present and not isinstance(nested_data, dict):
        return _failure("OTP verification failed")
    if direct_present:
        data = result["xSValidateDevice"]
    elif nested_present:
        data = nested_data
    else:
        data = None

    if isinstance(data, dict) and data.get("res") == "OK":
        return OTPVerificationSuccess(data)

    provider_message = data.get("msg") if isinstance(data, dict) else None
    provider_code = data.get("code") if isinstance(data, dict) else None
    return _failure(
        "OTP verification failed: invalid code"
        if _is_invalid_code_message(provider_message)
        else "OTP verification failed",
        provider_code,
    )

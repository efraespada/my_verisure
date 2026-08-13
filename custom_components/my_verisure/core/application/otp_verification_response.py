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


OTPVerificationDecision = OTPVerificationSuccess | OTPVerificationFailure


def classify_otp_verification_response(
    result: object,
) -> OTPVerificationDecision:
    """Classify an OTP verification response without side effects."""
    if not isinstance(result, dict):
        return OTPVerificationFailure("OTP verification failed: No response data")

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        message = (
            first_error.get("message", "Unknown error")
            if isinstance(first_error, dict)
            else "Unknown error"
        )
        return OTPVerificationFailure(f"OTP verification failed: {message}")

    wrapper = result.get("data")
    data = wrapper.get("xSValidateDevice") if isinstance(wrapper, dict) else None
    if not isinstance(data, dict):
        direct = result.get("xSValidateDevice")
        data = direct if isinstance(direct, dict) else None

    if isinstance(data, dict) and data.get("res") == "OK":
        return OTPVerificationSuccess(data)

    message = data.get("msg", "Unknown error") if isinstance(data, dict) else "No response data"
    return OTPVerificationFailure(f"OTP verification failed: {message}")

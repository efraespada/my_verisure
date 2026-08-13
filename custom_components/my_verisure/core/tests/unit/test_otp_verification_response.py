"""Contract tests for OTP verification response interpretation."""

from custom_components.my_verisure.core.application.otp_verification_response import (
    OTPVerificationFailure,
    OTPVerificationSuccess,
    classify_otp_verification_response,
)


def test_classifies_successful_graphql_envelope() -> None:
    result = classify_otp_verification_response(
        {"data": {"xSValidateDevice": {"res": "OK", "hash": "hash"}}}
    )

    assert isinstance(result, OTPVerificationSuccess)
    assert result.data["hash"] == "hash"


def test_classifies_graphql_error() -> None:
    result = classify_otp_verification_response(
        {"errors": [{"message": "invalid code"}]}
    )

    assert isinstance(result, OTPVerificationFailure)
    assert result.message == "OTP verification failed: invalid code"


def test_classifies_provider_failure_payload() -> None:
    result = classify_otp_verification_response(
        {"data": {"xSValidateDevice": {"res": "ERROR", "msg": "expired"}}}
    )

    assert isinstance(result, OTPVerificationFailure)
    assert result.message == "OTP verification failed: expired"


def test_classifies_empty_payload() -> None:
    result = classify_otp_verification_response({"data": {}})

    assert isinstance(result, OTPVerificationFailure)
    assert result.message == "OTP verification failed: No response data"

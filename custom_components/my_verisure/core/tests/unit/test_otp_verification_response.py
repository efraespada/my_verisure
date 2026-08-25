"""Contract tests for OTP verification response interpretation."""

from custom_components.my_verisure.core.api.otp_verification_response import (
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
    assert result.message == "OTP verification failed"
    assert result.retryable is False


def test_classifies_explicit_invalid_code_as_retryable() -> None:
    result = classify_otp_verification_response(
        {"data": {"xSValidateDevice": {"res": "ERROR", "msg": "invalid code"}}}
    )

    assert isinstance(result, OTPVerificationFailure)
    assert result.retryable is True


def test_classifies_empty_payload() -> None:
    result = classify_otp_verification_response({"data": {}})

    assert isinstance(result, OTPVerificationFailure)
    assert result.message == "OTP verification failed"


def test_rejects_ambiguous_otp_envelopes_and_redacts_provider_text() -> None:
    sentinel = "PROVIDER_SECRET_SENTINEL"
    result = classify_otp_verification_response(
        {
            "data": {"xSValidateDevice": {"res": "ERROR", "msg": sentinel}},
            "xSValidateDevice": {"res": "ERROR", "msg": sentinel},
        }
    )

    assert isinstance(result, OTPVerificationFailure)
    assert result.retryable is False
    assert result.message == "OTP verification failed"
    assert sentinel not in result.message


def test_rejects_multiple_graphql_errors_as_ambiguous() -> None:
    result = classify_otp_verification_response(
        {
            "errors": [
                {"message": "invalid code"},
                {"message": "terminal failure"},
            ]
        }
    )

    assert isinstance(result, OTPVerificationFailure)
    assert result.retryable is False
    assert result.message == "OTP verification failed"

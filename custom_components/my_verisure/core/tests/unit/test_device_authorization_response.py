"""Contract tests for device-authorization response interpretation."""

from custom_components.my_verisure.core.application.device_authorization_response import (
    DeviceAuthorizationFailure,
    DeviceAuthorizationOTPChallenge,
    DeviceAuthorizationSuccess,
    classify_device_authorization_response,
)


def test_classifies_successful_graphql_envelope() -> None:
    result = classify_device_authorization_response(
        {"data": {"xSValidateDevice": {"res": "OK", "hash": "hash"}}}
    )

    assert isinstance(result, DeviceAuthorizationSuccess)
    assert result.data == {"res": "OK", "hash": "hash"}


def test_classifies_otp_graphql_error() -> None:
    result = classify_device_authorization_response(
        {
            "errors": [
                {
                    "message": "authorization required",
                    "data": {"auth-code": "10001", "auth-type": "OTP"},
                }
            ]
        }
    )

    assert isinstance(result, DeviceAuthorizationOTPChallenge)
    assert result.data["auth-code"] == "10001"


def test_classifies_unauthorized_device() -> None:
    result = classify_device_authorization_response(
        {
            "errors": [
                {
                    "message": "unauthorized",
                    "data": {"auth-code": "10010"},
                }
            ]
        }
    )

    assert isinstance(result, DeviceAuthorizationFailure)
    assert result.unauthorized is True
    assert result.auth_code == "10010"


def test_classifies_unknown_provider_error() -> None:
    result = classify_device_authorization_response(
        {"errors": [{"message": "provider failure", "data": {"auth-code": "999"}}]}
    )

    assert isinstance(result, DeviceAuthorizationFailure)
    assert result.message == "Device validation failed: provider failure (auth-code: 999)"


def test_classifies_empty_payload() -> None:
    result = classify_device_authorization_response({"data": {}})

    assert isinstance(result, DeviceAuthorizationFailure)
    assert result.message == "No response data"


def test_accepts_legacy_direct_device_envelope() -> None:
    result = classify_device_authorization_response(
        {"xSValidateDevice": {"res": "OK", "hash": "hash"}}
    )

    assert isinstance(result, DeviceAuthorizationSuccess)

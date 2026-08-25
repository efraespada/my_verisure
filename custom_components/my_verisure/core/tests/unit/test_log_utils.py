"""Tests for log redaction and dev-mode context."""

from __future__ import annotations

import json

from custom_components.my_verisure.core import log_utils
from custom_components.my_verisure.core.application.models.auth import OTPData, Phone


def test_truncate_secret_short() -> None:
    """Short values are fully redacted."""
    out = log_utils.truncate_secret("abcdef")
    assert out == "[REDACTED]"


def test_truncate_secret_long_jwt_like() -> None:
    """Long secrets are fully redacted without a prefix."""
    token = "eyJ" + "a" * 80
    out = log_utils.truncate_secret(token)
    assert out == "[REDACTED]"


def test_redact_sensitive_data_removes_capabilities_header() -> None:
    """x-capabilities style keys are dropped from serialized output."""
    payload = {
        "numinst": "INSTALLATION_SENTINEL",
        "current_installation": "INSTALLATION_CURRENT_SENTINEL",
        "installation_id": "INSTALLATION_ID_SENTINEL",
        "x-capabilities": "LONG_CAPS",
        "other": 1,
    }
    s = log_utils.redact_sensitive_data(payload)
    data = json.loads(s)
    assert "x-capabilities" not in data
    assert data["numinst"] == "[REDACTED]"
    assert data["current_installation"] == "[REDACTED]"
    assert data["installation_id"] == "[REDACTED]"


def test_redact_sensitive_data_redacts_all_authentication_material() -> None:
    """No authentication material may appear in diagnostic/log payloads."""
    payload = {
        "password": "VALUE_PASSWORD",
        "hash": "VALUE_HASH",
        "refresh_token": "VALUE_REFRESH",
        "otp_code": "OTP_CODE_SENTINEL",
        "nested": {"authorization": "Bearer VALUE_TOKEN"},
    }

    serialized = log_utils.redact_sensitive_data(payload)

    for secret in (
        "VALUE_PASSWORD",
        "VALUE_HASH",
        "VALUE_REFRESH",
        "OTP_CODE_SENTINEL",
        "VALUE_TOKEN",
    ):
        assert secret not in serialized


def test_redact_sensitive_data_redacts_hash_completely() -> None:
    """Hash-like keys are fully redacted, never truncated."""
    payload = {"hash": "eyJ" + "x" * 100}
    s = log_utils.redact_sensitive_data(payload)
    data = json.loads(s)
    assert data["hash"] == "[REDACTED]"


def test_redact_sensitive_data_redacts_jwt_like_values_completely() -> None:
    """JWT-like values are redacted even when their key is not known."""
    payload = {"nested": "eyJ" + "a" * 80}
    serialized = log_utils.redact_sensitive_data(payload)
    data = json.loads(serialized)
    assert data["nested"] == "[REDACTED]"


def test_redact_sensitive_data_redacts_unknown_string_aliases() -> None:
    serialized = log_utils.redact_sensitive_data(
        {"futureSecretAlias": "UNKNOWN_SECRET_SENTINEL"}
    )

    assert "UNKNOWN_SECRET_SENTINEL" not in serialized
    assert "[REDACTED]" in serialized


def test_redact_headers_for_log_redacts_unknown_header_values() -> None:
    serialized = log_utils.redact_headers_for_log(
        {"X-Future-Secret": "UNKNOWN_HEADER_SECRET_SENTINEL"}
    )

    assert "UNKNOWN_HEADER_SECRET_SENTINEL" not in serialized


def test_redact_unknown_primitive_values_completely() -> None:
    serialized = log_utils.redact_sensitive_data(
        {"futureNumericSecret": 424242, "futureFlagSecret": True}
    )

    assert "424242" not in serialized
    assert "true" not in serialized.lower()
    assert serialized.count("[REDACTED]") == 2


def test_redact_unknown_numeric_header_value_completely() -> None:
    serialized = log_utils.redact_headers_for_log({"X-Future-Secret": 424242})

    assert "424242" not in serialized
    assert "[REDACTED]" in serialized


def test_redact_sensitive_data_redacts_identity_and_device_fields() -> None:
    """Identity/device fields never appear in serialized diagnostic payloads."""
    payload = {
        "user": "USER_SENTINEL",
        "username": "USER_SENTINEL",
        "phone": "PHONE_SENTINEL",
        "uuid": "UUID_SENTINEL",
        "deviceName": "DEVICE_SENTINEL",
        "record_id": "OTP_CODE_SENTINEL",
        "Security": "SECURITY_SENTINEL",
    }
    serialized = log_utils.redact_sensitive_data(payload)
    for value in payload.values():
        assert str(value) not in serialized
    assert serialized.count("[REDACTED]") == len(payload)


def test_redact_sensitive_data_redacts_provider_identifier_aliases() -> None:
    serialized = log_utils.redact_sensitive_data(
        {
            "referenceId": "REFERENCE_SENTINEL",
            "idService": "SERVICE_SENTINEL",
            "capabilities": "CAPABILITIES_SENTINEL",
            "panel": "PANEL_SENTINEL",
            "authCode": "AUTH_CODE_SENTINEL",
            "idSignal": "SIGNAL_SENTINEL",
            "path": "/private/path/SENTINEL",
            "error": "PROVIDER_ERROR_SENTINEL",
        }
    )
    for sentinel in (
        "REFERENCE_SENTINEL",
        "SERVICE_SENTINEL",
        "CAPABILITIES_SENTINEL",
        "PANEL_SENTINEL",
        "AUTH_CODE_SENTINEL",
        "SIGNAL_SENTINEL",
        "SENTINEL",
        "PROVIDER_ERROR_SENTINEL",
    ):
        assert sentinel not in serialized




def test_redact_sensitive_data_redacts_alias_and_name_variants() -> None:
    serialized = log_utils.redact_sensitive_data(
        {
            "alias": "ALIAS_SENTINEL",
            "name": "NAME_SENTINEL",
            "deviceAlias": "DEVICE_ALIAS_SENTINEL",
            "device_name": "DEVICE_NAME_SENTINEL",
            "nested": {"cameraName": "CAMERA_NAME_SENTINEL"},
        }
    )
    for sentinel in (
        "ALIAS_SENTINEL",
        "NAME_SENTINEL",
        "DEVICE_ALIAS_SENTINEL",
        "DEVICE_NAME_SENTINEL",
        "CAMERA_NAME_SENTINEL",
    ):
        assert sentinel not in serialized


def test_redact_sensitive_data_redacts_provider_messages() -> None:
    serialized = log_utils.redact_sensitive_data(
        {"message": "PROVIDER_MESSAGE_SENTINEL", "msg": "PROVIDER_MSG_SENTINEL"}
    )
    assert "PROVIDER_MESSAGE_SENTINEL" not in serialized
    assert "PROVIDER_MSG_SENTINEL" not in serialized


def test_redact_headers_for_log_strips_auth_hash() -> None:
    """Auth JSON header has a fully redacted hash."""
    import json as _json

    auth_inner = {"user": "u", "hash": "VALUE_HASH" * 20, "lang": "es"}
    headers = {"Content-Type": "application/json", "auth": _json.dumps(auth_inner)}
    s = log_utils.redact_headers_for_log(headers)
    assert "VALUE_HASH" * 20 not in s
    assert "[REDACTED]" in s


def test_redact_sensitive_data_redacts_provider_camel_case_and_exceptions() -> None:
    """Provider-shaped payloads and exception messages never leak."""
    payload = {
        "refreshToken": "REFRESH_SENTINEL",
        "otpHash": "OTP_HASH_SENTINEL",
        "recordId": "RECORD_SENTINEL",
        "deviceUUID": "UUID_SENTINEL",
        "id": "ID_SENTINEL",
        "error": RuntimeError("PROVIDER_ERROR_SENTINEL"),
    }

    serialized = log_utils.redact_sensitive_data(payload)

    for secret in (
        "REFRESH_SENTINEL",
        "OTP_HASH_SENTINEL",
        "RECORD_SENTINEL",
        "UUID_SENTINEL",
        "ID_SENTINEL",
        "PROVIDER_ERROR_SENTINEL",
    ):
        assert secret not in serialized


def test_redact_headers_for_log_redacts_security_and_identity_fields() -> None:
    """Auth and security headers must redact every sensitive nested value."""
    headers = {
        "auth": json.dumps({"user": "USER_SENTINEL", "hash": "HASH_SENTINEL"}),
        "Security": json.dumps({"token": "TOKEN_SENTINEL", "otpHash": "OTP_SENTINEL"}),
    }

    serialized = log_utils.redact_headers_for_log(headers)

    for secret in (
        "USER_SENTINEL",
        "HASH_SENTINEL",
        "TOKEN_SENTINEL",
        "OTP_SENTINEL",
    ):
        assert secret not in serialized


def test_redact_sensitive_data_redacts_dataclass_fields() -> None:
    """Dataclass authentication state is converted before redaction."""
    payload = OTPData(
        phones=[Phone(id=7, phone="PHONE_SENTINEL")],
        otp_hash="OTP_HASH_SENTINEL",
    )

    serialized = log_utils.redact_sensitive_data(payload)

    assert "PHONE_SENTINEL" not in serialized
    assert "OTP_HASH_SENTINEL" not in serialized


def test_redact_sensitive_data_redacts_tuple_and_unknown_objects() -> None:
    """Tuple DTOs and arbitrary objects cannot escape through repr serialization."""
    payload = {
        "phones": (Phone(id=7, phone="PHONE_TUPLE_SENTINEL"),),
        "unknown": object(),
    }

    serialized = log_utils.redact_sensitive_data(payload)

    assert "PHONE_TUPLE_SENTINEL" not in serialized
    assert "<object object>" not in serialized
    assert "[REDACTED]" in serialized


def test_dev_mode_context_isolation() -> None:
    """Dev mode flag resets after context."""
    assert log_utils.get_dev_mode() is False
    tok = log_utils.set_dev_mode(True)
    try:
        assert log_utils.get_dev_mode() is True
    finally:
        log_utils.reset_dev_mode(tok)
    assert log_utils.get_dev_mode() is False


def test_dev_mode_context_manager() -> None:
    """dev_mode_context restores previous value."""
    assert log_utils.get_dev_mode() is False
    with log_utils.dev_mode_context(True):
        assert log_utils.get_dev_mode() is True
    assert log_utils.get_dev_mode() is False

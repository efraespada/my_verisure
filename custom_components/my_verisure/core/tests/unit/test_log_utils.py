"""Tests for log redaction and dev-mode context."""

from __future__ import annotations

import json

from custom_components.my_verisure.core import log_utils


def test_truncate_secret_short() -> None:
    """Very short values are abbreviated."""
    out = log_utils.truncate_secret("abcdef")
    assert "…" in out or "..." in out


def test_truncate_secret_long_jwt_like() -> None:
    """Long secrets show prefix only."""
    token = "eyJ" + "a" * 80
    out = log_utils.truncate_secret(token)
    assert out.endswith("...")
    assert len(out) < len(token)


def test_redact_sensitive_data_removes_capabilities_header() -> None:
    """x-capabilities style keys are dropped from serialized output."""
    payload = {"numinst": "1", "x-capabilities": "LONG_CAPS", "other": 1}
    s = log_utils.redact_sensitive_data(payload)
    data = json.loads(s)
    assert "x-capabilities" not in data
    assert data["numinst"] == "1"


def test_redact_sensitive_data_redacts_all_authentication_material() -> None:
    """No authentication material may appear in diagnostic/log payloads."""
    payload = {
        "password": "secret-password",
        "hash": "secret-hash",
        "refresh_token": "secret-refresh-token",
        "otp_code": "123456",
        "nested": {"authorization": "Bearer secret-token"},
    }

    serialized = log_utils.redact_sensitive_data(payload)

    for secret in (
        "secret-password",
        "secret-hash",
        "secret-refresh-token",
        "123456",
        "secret-token",
    ):
        assert secret not in serialized


def test_redact_sensitive_data_truncates_hash() -> None:
    """Hash-like keys are truncated."""
    payload = {"hash": "eyJ" + "x" * 100}
    s = log_utils.redact_sensitive_data(payload)
    data = json.loads(s)
    assert data["hash"].endswith("...")
    assert len(data["hash"]) < 50


def test_redact_headers_for_log_strips_auth_hash() -> None:
    """Auth JSON header has truncated hash."""
    import json as _json

    auth_inner = {"user": "u", "hash": "secret" * 20, "lang": "es"}
    headers = {"Content-Type": "application/json", "auth": _json.dumps(auth_inner)}
    s = log_utils.redact_headers_for_log(headers)
    assert "secret" * 20 not in s
    assert "..." in s


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

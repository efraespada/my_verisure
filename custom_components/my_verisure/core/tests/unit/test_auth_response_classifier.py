"""Tests for authentication response classification."""

from custom_components.my_verisure.core.api.auth_response_classifier import (
    LoginResponse,
    classify_login_response,
)


def test_classify_login_success() -> None:
    result = classify_login_response(
        {"data": {"xSLoginToken": {"res": "OK", "hash": "token"}}}
    )
    assert isinstance(result, LoginResponse)
    assert result.data["hash"] == "token"


def test_classify_invalid_credentials_error() -> None:
    assert (
        classify_login_response(
            {"errors": [{"message": "denied", "data": {"err": "60091"}}]}
        )
        == "Invalid user or password"
    )


def test_classify_empty_errors_as_failed_response() -> None:
    assert classify_login_response({"errors": []}) == "Authentication response failed"
    assert classify_login_response(None) == "Authentication response unavailable"
    assert classify_login_response({"data": {"xSLoginToken": {"res": "ERROR", "msg": "bad"}}}) == "Authentication response failed"
    assert classify_login_response({"data": {}}) == "Authentication response unavailable"

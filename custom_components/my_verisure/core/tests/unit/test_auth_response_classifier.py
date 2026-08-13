"""Tests for authentication response classification."""

from custom_components.my_verisure.core.application.auth_response_classifier import (
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


def test_classify_malformed_and_failed_responses() -> None:
    assert classify_login_response(None) == "No response data"
    assert classify_login_response({"data": {"xSLoginToken": {"res": "ERROR", "msg": "bad"}}}) == "Login failed: bad"
    assert classify_login_response({"data": {}}) == "Login failed: No response data"

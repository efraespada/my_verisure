"""Pure response classification for authentication GraphQL payloads."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LoginResponse:
    """Validated login payload returned by the provider."""

    data: dict[str, Any]


def classify_login_response(result: object) -> LoginResponse | str:
    """Return validated login data or a provider error message."""
    if not isinstance(result, dict):
        return "Authentication response unavailable"

    if "errors" in result:
        errors = result["errors"]
        if not isinstance(errors, list) or len(errors) != 1:
            return "Authentication response failed"
        first_error = errors[0]
        if isinstance(first_error, dict):
            error_data = first_error.get("data")
            if isinstance(error_data, dict) and error_data.get("err") == "60091":
                return "Invalid user or password"
        return "Authentication failed"

    wrapper_present = "data" in result
    wrapper = result.get("data")
    if wrapper_present and not isinstance(wrapper, dict):
        return "Authentication response failed"
    nested_present = isinstance(wrapper, dict) and "xSLoginToken" in wrapper
    direct_present = "xSLoginToken" in result
    if direct_present and nested_present:
        return "Authentication response failed"
    login_data = (
        wrapper.get("xSLoginToken")
        if nested_present and isinstance(wrapper, dict)
        else result.get("xSLoginToken")
        if direct_present
        else None
    )
    if isinstance(login_data, dict) and login_data.get("res") == "OK":
        # Current native responses select this nullable field. A successful,
        # token-bearing native login is the explicit authorization signal.
        if (
            "needDeviceAuthorization" in login_data
            and login_data["needDeviceAuthorization"] is None
            and login_data.get("msg") == "auth-api.login.success"
            and isinstance(login_data.get("hash"), str) and login_data["hash"].strip()
            and isinstance(login_data.get("refreshToken"), str) and login_data["refreshToken"].strip()
        ):
            login_data = {**login_data, "needDeviceAuthorization": False}
        return LoginResponse(data=login_data)

    if direct_present or nested_present:
        return "Authentication response failed"
    return "Authentication response unavailable"

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
        return "No response data"

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first_error = errors[0]
        if isinstance(first_error, dict):
            error_data = first_error.get("data")
            if isinstance(error_data, dict) and error_data.get("err") == "60091":
                return "Invalid user or password"
            return f"Login failed: {first_error.get('message', 'Unknown error')}"
        return "Login failed: Unknown error"

    wrapper = result.get("data")
    login_data = wrapper.get("xSLoginToken") if isinstance(wrapper, dict) else None
    if isinstance(login_data, dict) and login_data.get("res") == "OK":
        return LoginResponse(data=login_data)

    if isinstance(login_data, dict):
        return f"Login failed: {login_data.get('msg', 'Unknown error')}"
    return "Login failed: No response data"

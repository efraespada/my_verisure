"""Provider-auth response projection into application session data."""

from __future__ import annotations

from typing import Any

from ..application.exceptions import MyVerisurePersistenceError


def build_session_data(
    user: str, login_data: dict[str, Any], login_time: int
) -> dict[str, Any]:
    """Translate a validated provider login envelope to session data."""
    need_device_authorization = login_data.get("needDeviceAuthorization")
    if not isinstance(need_device_authorization, bool):
        raise MyVerisurePersistenceError("Authentication response failed")
    session_data: dict[str, Any] = {
        "user": user,
        "needDeviceAuthorization": need_device_authorization,
        "login_time": login_time,
    }
    optional_fields = {
        "lang": str,
        "legals": bool,
        "changePassword": bool,
    }
    for field, expected_type in optional_fields.items():
        if field not in login_data:
            continue
        value = login_data[field]
        if expected_type is str and (not isinstance(value, str) or not value.strip()):
            raise MyVerisurePersistenceError("Authentication response failed")
        if expected_type is bool and not isinstance(value, bool):
            raise MyVerisurePersistenceError("Authentication response failed")
        session_data[field] = value
    return session_data

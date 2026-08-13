"""Pure interpretation of installation GraphQL payloads."""

from __future__ import annotations

from typing import Any


class InstallationResponseError(ValueError):
    """Provider response cannot be interpreted as an installation payload."""


def _raise_graphql_error(result: dict[str, Any], operation: str) -> None:
    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        message = first.get("message", "Unknown error") if isinstance(first, dict) else "Unknown error"
        raise InstallationResponseError(f"Failed to get {operation}: {message}")


def interpret_installations(result: object) -> list[dict[str, Any]]:
    """Return raw installation records from the provider payload."""
    if not isinstance(result, dict):
        raise InstallationResponseError("Failed to get installations: No response data")
    _raise_graphql_error(result, "installations")
    data = result.get("data")
    wrapper = data.get("xSInstallations") if isinstance(data, dict) else None
    records = wrapper.get("installations") if isinstance(wrapper, dict) else None
    if records is None:
        raise InstallationResponseError("Failed to get installations: No response data")
    if not isinstance(records, list):
        raise InstallationResponseError("Failed to get installations: Invalid installations data")
    return [record for record in records if isinstance(record, dict)]


def interpret_services(result: object) -> dict[str, Any]:
    """Return the successful service installation record."""
    if not isinstance(result, dict):
        raise InstallationResponseError("Failed to get installation services: No response data")
    _raise_graphql_error(result, "installation services")
    data = result.get("data")
    services = data.get("xSSrv") if isinstance(data, dict) else None
    if not isinstance(services, dict) or services.get("res") != "OK":
        message = services.get("msg", "No response data") if isinstance(services, dict) else "No response data"
        raise InstallationResponseError(f"Failed to get installation services: {message}")
    installation = services.get("installation")
    if not isinstance(installation, dict):
        raise InstallationResponseError("Failed to get installation services: No installation data")
    return {"installation": installation, "language": services.get("language")}


def interpret_devices(result: object) -> list[dict[str, Any]]:
    """Return raw device records from the provider payload."""
    if not isinstance(result, dict):
        raise InstallationResponseError("Failed to get installation devices: No response data")
    _raise_graphql_error(result, "installation devices")
    data = result.get("data")
    devices_data = data.get("xSDeviceList") if isinstance(data, dict) else None
    if not isinstance(devices_data, dict) or devices_data.get("res") != "OK":
        message = devices_data.get("msg", "No response data") if isinstance(devices_data, dict) else "No response data"
        raise InstallationResponseError(f"Failed to get installation devices: {message}")
    devices = devices_data.get("devices", [])
    if not isinstance(devices, list):
        raise InstallationResponseError("Failed to get installation devices: Invalid devices data")
    return [device for device in devices if isinstance(device, dict)]

"""Diagnostics support for My Verisure."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .core.const import CONF_INSTALLATION_ID, CONF_PASSWORD, CONF_USER
from .coordinator import MyVerisureDataUpdateCoordinator

REDACT_KEYS = {
    CONF_PASSWORD,
    CONF_USER,
    CONF_INSTALLATION_ID,
    "password",
    "hash",
    "refresh_token",
    "hash_token",
    "token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = entry.runtime_data

    entry_dict = entry.as_dict()
    redacted_entry = async_redact_data(entry_dict, REDACT_KEYS)

    data_summary: dict[str, Any] = {}
    if coordinator.data:
        data_summary = {
            "has_alarm_status": "alarm_status" in coordinator.data,
            "has_detailed_installation": "detailed_installation"
            in coordinator.data,
            "last_updated": coordinator.data.get("last_updated"),
        }

    session_info: dict[str, Any] = {}
    try:
        session_info = {
            "is_authenticated": coordinator.session_manager.is_authenticated,
            "session_valid": coordinator.session_manager.is_session_valid(),
        }
    except Exception:
        session_info = {"error": "Unable to collect session diagnostics"}

    return {
        "entry": redacted_entry,
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
            "data_summary": data_summary,
            "session": session_info,
        },
    }

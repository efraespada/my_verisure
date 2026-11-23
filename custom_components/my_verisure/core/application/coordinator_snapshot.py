"""Application services for composing coordinator snapshots.

The functions in this module are deliberately independent from Home Assistant,
filesystem adapters, and network clients. They define the application payload
that adapters may persist or expose.
"""

from __future__ import annotations

from typing import Any, Mapping

from .alarm_state import analyze_alarm_state


def build_coordinator_snapshot(
    *,
    installation_id: str,
    alarm_status: Mapping[str, Any],
    detailed_installation: Mapping[str, Any],
    timestamp: float,
) -> dict[str, Any]:
    """Build the canonical persisted coordinator snapshot."""
    return {
        "last_updated": timestamp,
        "installation_id": installation_id,
        "alarm_status": dict(alarm_status),
        "detailed_installation": dict(detailed_installation),
    }


def merge_alarm_snapshot(
    *,
    installation_id: str,
    alarm_status: Mapping[str, Any],
    detailed_installation: Mapping[str, Any],
    timestamp: float,
) -> dict[str, Any]:
    """Build a snapshot after an alarm-only refresh.

    Keeping this as a separate named operation makes the reduced refresh path
    explicit and prevents it from silently dropping installation data.
    """
    return build_coordinator_snapshot(
        installation_id=installation_id,
        alarm_status=alarm_status,
        detailed_installation=detailed_installation,
        timestamp=timestamp,
    )


def persistable_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Project runtime data to a secret-free, provider-agnostic snapshot."""
    alarm_payload = payload.get("alarm_status")
    if not isinstance(alarm_payload, dict):
        raise ValueError("invalid alarm snapshot")
    alarm_data = alarm_payload.get("data")
    if alarm_data is not None and not isinstance(alarm_data, dict):
        raise ValueError("invalid alarm snapshot data")
    alarm = analyze_alarm_state(alarm_payload)
    installation = payload.get("detailed_installation", {})
    raw_installation = (
        installation.get("installation", {}) if isinstance(installation, dict) else {}
    )
    safe_installation: dict[str, Any] = {}
    services = raw_installation.get("services", [])
    if not isinstance(services, list):
        raise ValueError("invalid installation services")
    safe_services: list[dict[str, bool]] = []
    for service in services:
        if (
            not isinstance(service, dict)
            or not isinstance(service.get("active"), bool)
            or not isinstance(service.get("visible"), bool)
        ):
            raise ValueError("invalid installation service")
        safe_services.append(
            {"active": service["active"], "visible": service["visible"]}
        )
    safe_installation["services"] = safe_services
    return {
        "last_updated": payload.get("last_updated"),
        "alarm_status": {
            "data": {
                "internal": {
                    "day": {"status": alarm.internal_day},
                    "night": {"status": alarm.internal_night},
                    "total": {"status": alarm.internal_total},
                },
                "external": {"status": alarm.external},
            }
        },
        "detailed_installation": {"installation": safe_installation},
    }

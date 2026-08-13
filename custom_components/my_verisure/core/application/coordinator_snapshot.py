"""Application services for composing coordinator snapshots.

The functions in this module are deliberately independent from Home Assistant,
filesystem adapters, and network clients. They define the application payload
that adapters may persist or expose.
"""

from __future__ import annotations

from typing import Any, Mapping


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

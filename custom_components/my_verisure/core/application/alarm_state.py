"""Application-level alarm state analysis.

This module contains no Home Assistant dependencies. It translates the Verisure
alarm payload into a stable application snapshot that adapters can expose using
platform-specific enums and attributes.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class AlarmState(StrEnum):
    """Normalized alarm states understood by the application layer."""

    DISARMED = "disarmed"
    ARMED_AWAY = "armed_away"
    ARMED_NIGHT = "armed_night"
    ARMED_HOME = "armed_home"


@dataclass(frozen=True)
class AlarmStateSnapshot:
    """Normalized alarm state and its detailed active modes."""

    state: AlarmState
    internal_day: bool = False
    internal_night: bool = False
    internal_total: bool = False
    external: bool = False

    @property
    def active_alarms(self) -> tuple[str, ...]:
        """Return human-readable active alarm modes in stable order."""
        active: list[str] = []
        if self.internal_total:
            active.append("Internal Total")
        if self.internal_day:
            active.append("Internal Day")
        if self.internal_night:
            active.append("Internal Night")
        if self.external:
            active.append("External")
        return tuple(active)


def analyze_alarm_state(alarm_data: dict[str, Any] | None) -> AlarmStateSnapshot:
    """Normalize a Verisure alarm payload into an application snapshot."""
    raw_data = (alarm_data or {}).get("data", {})
    if not isinstance(raw_data, dict):
        return AlarmStateSnapshot(AlarmState.DISARMED)

    internal = raw_data.get("internal", {})
    external = raw_data.get("external", {})
    if not isinstance(internal, dict) or not isinstance(external, dict):
        return AlarmStateSnapshot(AlarmState.DISARMED)

    internal_day = bool(_status(internal, "day"))
    internal_night = bool(_status(internal, "night"))
    internal_total = bool(_status(internal, "total"))
    external_status = bool(external.get("status", False))

    if internal_total:
        state = AlarmState.ARMED_AWAY
    elif internal_night:
        state = AlarmState.ARMED_NIGHT
    elif internal_day or external_status:
        state = AlarmState.ARMED_HOME
    else:
        state = AlarmState.DISARMED

    return AlarmStateSnapshot(
        state=state,
        internal_day=internal_day,
        internal_night=internal_night,
        internal_total=internal_total,
        external=external_status,
    )


def _status(section: dict[str, Any], mode: str) -> bool:
    """Read one mode status defensively from an upstream payload."""
    value = section.get(mode, {})
    return value.get("status", False) if isinstance(value, dict) else False

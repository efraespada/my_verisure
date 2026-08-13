"""Alarm command metadata used by the HA coordinator adapter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoordinatorAlarmCommand:
    """Translation and notification keys for one alarm command."""

    operation: str
    success_key: str
    error_key: str
    exception_key: str
    notification_id: str
    auto_arm_perimeter: bool = False


COMMANDS: dict[str, CoordinatorAlarmCommand] = {
    "arm_away": CoordinatorAlarmCommand(
        operation="arm_away",
        success_key="notifications.alarm.arm_away.success",
        error_key="notifications.alarm.arm_away.error",
        exception_key="notifications.alarm.arm_away.exception",
        notification_id="verisure_alarm_arm_away",
        auto_arm_perimeter=True,
    ),
    "arm_home": CoordinatorAlarmCommand(
        operation="arm_home",
        success_key="notifications.alarm.arm_home.success",
        error_key="notifications.alarm.arm_home.error",
        exception_key="notifications.alarm.arm_home.exception",
        notification_id="verisure_alarm_arm_home",
    ),
    "arm_night": CoordinatorAlarmCommand(
        operation="arm_night",
        success_key="notifications.alarm.arm_night.success",
        error_key="notifications.alarm.arm_night.error",
        exception_key="notifications.alarm.arm_night.exception",
        notification_id="verisure_alarm_arm_night",
        auto_arm_perimeter=True,
    ),
    "disarm": CoordinatorAlarmCommand(
        operation="disarm",
        success_key="notifications.alarm.disarm.success",
        error_key="notifications.alarm.disarm.error",
        exception_key="notifications.alarm.disarm.exception",
        notification_id="verisure_alarm_disarm",
    ),
}

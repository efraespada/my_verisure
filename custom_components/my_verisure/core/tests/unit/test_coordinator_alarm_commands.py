"""Tests for coordinator alarm command metadata."""

from custom_components.my_verisure.core.application.coordinator_alarm_commands import (
    COMMANDS,
)


def test_all_alarm_operations_have_complete_notification_metadata():
    assert set(COMMANDS) == {"arm_away", "arm_home", "arm_night", "disarm"}
    for command in COMMANDS.values():
        assert command.operation
        assert command.success_key.startswith("notifications.")
        assert command.error_key.startswith("notifications.")
        assert command.exception_key.startswith("notifications.")
        assert command.notification_id.startswith("verisure_alarm_")


def test_only_modes_with_perimeter_option_enable_it():
    assert COMMANDS["arm_away"].auto_arm_perimeter is True
    assert COMMANDS["arm_night"].auto_arm_perimeter is True
    assert COMMANDS["arm_home"].auto_arm_perimeter is False
    assert COMMANDS["disarm"].auto_arm_perimeter is False

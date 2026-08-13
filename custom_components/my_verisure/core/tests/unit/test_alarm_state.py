"""Tests for application-level alarm state analysis."""

import pytest

from custom_components.my_verisure.core.application.alarm_state import (
    AlarmState,
    analyze_alarm_state,
)


@pytest.mark.parametrize(
    ("payload", "state", "active"),
    [
        ({}, AlarmState.DISARMED, ()),
        ({"data": {}}, AlarmState.DISARMED, ()),
        (
            {"data": {"internal": {"day": {"status": True}}}},
            AlarmState.ARMED_HOME,
            ("Internal Day",),
        ),
        (
            {"data": {"internal": {"night": {"status": True}}}},
            AlarmState.ARMED_NIGHT,
            ("Internal Night",),
        ),
        (
            {"data": {"internal": {"total": {"status": True}}}},
            AlarmState.ARMED_AWAY,
            ("Internal Total",),
        ),
        (
            {"data": {"external": {"status": True}}},
            AlarmState.ARMED_HOME,
            ("External",),
        ),
    ],
)
def test_analyze_alarm_state(payload, state, active):
    snapshot = analyze_alarm_state(payload)

    assert snapshot.state is state
    assert snapshot.active_alarms == active


def test_total_has_priority_and_preserves_all_active_modes():
    snapshot = analyze_alarm_state(
        {
            "data": {
                "internal": {
                    "day": {"status": True},
                    "night": {"status": True},
                    "total": {"status": True},
                },
                "external": {"status": True},
            }
        }
    )

    assert snapshot.state is AlarmState.ARMED_AWAY
    assert snapshot.active_alarms == (
        "Internal Total",
        "Internal Day",
        "Internal Night",
        "External",
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"data": None},
        {"data": []},
        {"data": {"internal": [], "external": {}}},
        {"data": {"internal": {}, "external": []}},
    ],
)
def test_analyze_alarm_state_is_defensive(payload):
    assert analyze_alarm_state(payload).state is AlarmState.DISARMED

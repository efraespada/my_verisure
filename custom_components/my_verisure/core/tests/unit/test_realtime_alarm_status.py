"""Tests for realtime alarm status interpretation."""

import pytest

from custom_components.my_verisure.core.application.realtime_alarm_status import (
    RealtimeAlarmStatusInterpreter,
    RealtimeStatusAction,
)


@pytest.mark.parametrize(
    ("result", "action", "message"),
    [
        (
            {"data": {"xSCheckAlarmStatus": {"res": "OK", "msg": "armed"}}},
            RealtimeStatusAction.SUCCESS,
            "armed",
        ),
        (
            {"data": {"xSCheckAlarmStatus": {"res": "KO", "msg": "failed"}}},
            RealtimeStatusAction.FAILURE,
            "failed",
        ),
        (
            {"data": {"xSCheckAlarmStatus": {"res": "WAIT", "msg": "pending"}}},
            RealtimeStatusAction.WAIT,
            "pending",
        ),
        (
            {"data": {"xSCheckAlarmStatus": {"res": "UNKNOWN", "msg": "?"}}},
            RealtimeStatusAction.EMPTY,
            "",
        ),
        ({"errors": [{"message": "upstream"}]}, RealtimeStatusAction.EMPTY, ""),
        ({}, RealtimeStatusAction.EMPTY, ""),
    ],
)
def test_interpret_realtime_status(result, action, message):
    decision = RealtimeAlarmStatusInterpreter().interpret(result)

    assert decision.action is action
    assert decision.message == message

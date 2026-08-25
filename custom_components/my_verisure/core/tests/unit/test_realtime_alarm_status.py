"""Tests for realtime alarm status interpretation."""

import pytest

from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.api.realtime_alarm_status import (
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
    ],
)
def test_interpret_realtime_status(result, action, message):
    decision = RealtimeAlarmStatusInterpreter().interpret(result)

    assert decision.action is action
    assert decision.message == message


@pytest.mark.parametrize("result", [{"errors": []}, {"errors": None}, {}])
def test_interpret_realtime_status_rejects_ambiguous_envelopes(result):
    with pytest.raises(MyVerisureError, match="realtime alarm status response"):
        RealtimeAlarmStatusInterpreter().interpret(result)




def test_response_fields_rejects_missing_message():
    with pytest.raises(MyVerisureError, match="realtime alarm status response"):
        RealtimeAlarmStatusInterpreter._response_fields({"res": "OK"})


def test_response_fields_rejects_missing_result_code():
    with pytest.raises(MyVerisureError, match="realtime alarm status response"):
        RealtimeAlarmStatusInterpreter._response_fields({})


@pytest.mark.parametrize("result", [None, [], {"data": []}])
def test_interpret_realtime_status_rejects_non_mapping_envelopes(result):
    with pytest.raises(MyVerisureError, match="realtime alarm status response"):
        RealtimeAlarmStatusInterpreter().interpret(result)

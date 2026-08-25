"""Tests for initial alarm command response interpretation."""

import pytest

from custom_components.my_verisure.core.api.alarm_command_response import (
    AlarmCommandResponseInterpreter,
)


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (
            {"data": {"xSArmPanel": {"res": "OK", "msg": "armed", "referenceId": 7}}},
            (True, "Alarm command accepted", "7"),
        ),
        (
            {"data": {"xSDisarmPanel": {"res": "KO", "msg": "rejected", "referenceId": "ref"}}},
            (False, "Alarm command rejected", None),
        ),
        (
            {"errors": [{"message": "upstream failure"}]},
            (False, "Alarm service request failed", None),
        ),
        ({}, (False, "Alarm command rejected", None)),
        ({"errors": []}, (False, "Alarm service request failed", None)),
    ],
)
def test_interpret_command_response(result, expected):
    payload_key = "xSArmPanel" if "xSArmPanel" in str(result) else "xSDisarmPanel"

    response = AlarmCommandResponseInterpreter().interpret(
        result,
        payload_key=payload_key,
    )

    assert (response.accepted, response.message, response.reference_id) == expected

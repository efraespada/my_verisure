"""Tests for initial alarm command response interpretation."""

import pytest

from custom_components.my_verisure.core.application.alarm_command_response import (
    AlarmCommandResponseInterpreter,
)


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (
            {"data": {"xSArmPanel": {"res": "OK", "msg": "armed", "referenceId": 7}}},
            (True, "armed", "7"),
        ),
        (
            {"data": {"xSDisarmPanel": {"res": "KO", "msg": "rejected", "referenceId": "ref"}}},
            (False, "rejected", None),
        ),
        (
            {"errors": [{"message": "upstream failure"}]},
            (False, "upstream failure", None),
        ),
        ({}, (False, "Unknown", None)),
    ],
)
def test_interpret_command_response(result, expected):
    payload_key = "xSArmPanel" if "xSArmPanel" in str(result) else "xSDisarmPanel"

    response = AlarmCommandResponseInterpreter().interpret(
        result,
        payload_key=payload_key,
    )

    assert (response.accepted, response.message, response.reference_id) == expected

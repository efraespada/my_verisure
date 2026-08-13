"""Tests for alarm GraphQL request definitions."""

from custom_components.my_verisure.core.application.alarm_graphql_requests import (
    AlarmGraphQLRequestPolicy,
)


def test_arm_panel_request_preserves_verisure_contract() -> None:
    request = AlarmGraphQLRequestPolicy.arm_panel("home-1", "panel", "ARM1", "E")

    assert request.operation == "ArmPanel"
    assert request.variables == {
        "numinst": "home-1",
        "request": "ARM1",
        "panel": "panel",
        "currentStatus": "E",
        "forceArmingRemoteId": None,
        "armAndLock": False,
    }


def test_check_alarm_status_request_uses_provider_field_names() -> None:
    request = AlarmGraphQLRequestPolicy.check_alarm_status(
        "home-1", "panel", "EST", "reference"
    )

    assert request.operation == "CheckAlarmStatus"
    assert request.variables == {
        "numinst": "home-1",
        "panel": "panel",
        "idService": "EST",
        "referenceId": "reference",
    }


def test_disarm_status_request_contains_counter_and_reference() -> None:
    request = AlarmGraphQLRequestPolicy.disarm_status(
        "home-1", "panel", "DARM1", "reference", 3
    )

    assert request.operation == "DisarmStatus"
    assert request.variables["counter"] == 3
    assert request.variables["referenceId"] == "reference"

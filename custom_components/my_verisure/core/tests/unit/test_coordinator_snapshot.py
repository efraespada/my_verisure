"""Tests for canonical coordinator snapshot construction."""

from custom_components.my_verisure.core.application.coordinator_snapshot import (
    build_coordinator_snapshot,
    merge_alarm_snapshot,
)


def test_build_snapshot_has_stable_application_shape():
    result = build_coordinator_snapshot(
        installation_id="home-1",
        alarm_status={"status": "armed"},
        detailed_installation={"installation": {"panel": "P1"}},
        timestamp=123.0,
    )

    assert result == {
        "last_updated": 123.0,
        "installation_id": "home-1",
        "alarm_status": {"status": "armed"},
        "detailed_installation": {"installation": {"panel": "P1"}},
    }


def test_merge_alarm_snapshot_preserves_installation_payload():
    result = merge_alarm_snapshot(
        installation_id="home-1",
        alarm_status={"status": "disarmed"},
        detailed_installation={"installation": {"panel": "P1"}},
        timestamp=124.0,
    )

    assert result["detailed_installation"]["installation"]["panel"] == "P1"
    assert result["alarm_status"] == {"status": "disarmed"}

"""Tests for the alarm status application service."""

import pytest
from pathlib import Path

from custom_components.my_verisure.core.application.alarm_status_service import (
    AlarmStatusService,
)
from custom_components.my_verisure.core.application.alarm_state import (
    AlarmState,
    analyze_alarm_state,
)


@pytest.mark.asyncio
async def test_process_message_maps_internal_and_external_categories(tmp_path: Path):
    service = AlarmStatusService(
        tmp_path / "status.json",
        read_config=lambda _: {
            "internal": {"day": {"alarm": ["day-alarm"]}},
            "external": {"alarm": ["external-alarm"]},
        },
    )

    day_status = await service.process_message("day-alarm")
    external_status = await service.process_message("external-alarm")

    assert day_status["internal"]["day"]["status"] is True
    assert day_status["external"]["status"] is False
    assert external_status["external"]["status"] is True


@pytest.mark.asyncio
async def test_empty_message_returns_default_status(tmp_path: Path):
    service = AlarmStatusService(tmp_path / "status.json")

    assert await service.process_message("") == service.default_status()


@pytest.mark.asyncio
async def test_unknown_message_preserves_unknown_status(tmp_path: Path):
    service = AlarmStatusService(
        tmp_path / "status.json",
        read_config=lambda _: {"internal": {}, "external": {}},
    )

    result = await service.process_message("unrecognized")

    assert result == service.default_status()
    assert result["internal"]["total"]["status"] is None
    assert result["external"]["status"] is None


@pytest.mark.asyncio
async def test_configuration_is_cached_per_service_instance(tmp_path: Path):
    reads: list[str] = []

    def read_config(path: str):
        reads.append(path)
        return {"owner": "one"}

    service = AlarmStatusService(tmp_path / "status.json", read_config=read_config)

    assert await service.load_config() == {"owner": "one"}
    assert await service.load_config() == {"owner": "one"}
    assert reads == [str(tmp_path / "status.json")]


@pytest.mark.asyncio
async def test_invalid_json_uses_safe_fallback(tmp_path: Path):
    config_path = tmp_path / "status.json"
    config_path.write_text("not-json", encoding="utf-8")
    service = AlarmStatusService(config_path)

    assert await service.load_config() == {
        "internal": {
            "day": {"alarm": []},
            "night": {"alarm": []},
            "total": {"alarm": []},
        },
        "external": {"alarm": []},
    }


@pytest.mark.asyncio
async def test_missing_file_uses_safe_fallback(tmp_path: Path):
    service = AlarmStatusService(tmp_path / "missing.json")

    assert await service.process_message("unknown") == service.default_status()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message, expected, exterior",
    [
        ("alarm-manager.inactive_alarm", AlarmState.DISARMED, False),
        ("alarm-manager.active_partial_day_alarm", AlarmState.ARMED_HOME, False),
        ("alarm-manager.active_partial_night_alarm", AlarmState.ARMED_NIGHT, False),
        ("alarm-manager.status.active_alarm_msg", AlarmState.ARMED_AWAY, False),
        ("alarm-manager.status_panel.active_perimetral_alarm_msg", AlarmState.ARMED_HOME, True),
        ("alarm-manager.active_partial_day_plus_perimeter", AlarmState.ARMED_HOME, True),
        ("alarm-manager.active_partial_night_plus_perimeter", AlarmState.ARMED_NIGHT, True),
        ("alarm-manager.active_perimeter_plus_alarm", AlarmState.ARMED_AWAY, True),
    ],
)
async def test_bundled_complete_provider_messages_resolve_all_zone_states(
    message, expected, exterior
):
    config_path = Path(__file__).parents[2] / "api" / "alarm_status.json"
    status = await AlarmStatusService(config_path).process_message(message)

    snapshot = analyze_alarm_state({"data": status})

    assert snapshot.state == expected
    assert snapshot.external is exterior
    assert all(
        value is not None
        for value in (
            snapshot.internal_day,
            snapshot.internal_night,
            snapshot.internal_total,
            snapshot.external,
        )
    )

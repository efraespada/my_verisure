"""Tests for the alarm status application service."""

import json
from pathlib import Path

import pytest

from custom_components.my_verisure.core.application.alarm_status_service import (
    AlarmStatusService,
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

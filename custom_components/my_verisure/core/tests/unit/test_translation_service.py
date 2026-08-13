"""Tests for translation loading and resolution."""

import json

import pytest

from custom_components.my_verisure.core.application.translation_service import (
    TranslationService,
)


@pytest.mark.asyncio
async def test_translation_service_resolves_nested_key_and_formats(tmp_path):
    (tmp_path / "en.json").write_text(
        json.dumps({"notifications": {"alarm": {"failed": "Failed: {message}"}}}),
        encoding="utf-8",
    )

    result = await TranslationService(tmp_path).get(
        "en", "notifications.alarm.failed", message="offline"
    )

    assert result == "Failed: offline"


@pytest.mark.asyncio
async def test_translation_service_falls_back_to_english_and_key(tmp_path):
    (tmp_path / "en.json").write_text(
        json.dumps({"known": "English"}), encoding="utf-8"
    )
    service = TranslationService(tmp_path)

    assert await service.get("es", "known") == "English"
    assert await service.get("es", "missing.key") == "missing.key"


@pytest.mark.asyncio
async def test_translation_service_handles_invalid_json_and_missing_format_arg(tmp_path):
    (tmp_path / "en.json").write_text("not-json", encoding="utf-8")
    service = TranslationService(tmp_path)

    assert await service.get("en", "missing") == "missing"

    (tmp_path / "en.json").write_text(
        json.dumps({"message": "Hello {name}"}), encoding="utf-8"
    )
    assert await service.get("en", "message") == "Hello {name}"

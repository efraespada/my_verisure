"""Translation loading and key resolution for the integration."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any


class TranslationService:
    """Load localized JSON resources without blocking the event loop."""

    def __init__(self, translations_dir: Path) -> None:
        self._translations_dir = translations_dir

    async def get(self, language: str | None, key: str, **kwargs: object) -> str:
        """Resolve and format one translation, falling back to English."""
        language_data = await self._load(language or "en")
        if language_data is None and language != "en":
            language_data = await self._load("en")
        return self._resolve(language_data or {}, key, kwargs)

    async def _load(self, language: str) -> dict[str, Any] | None:
        path = self._translations_dir / f"{language}.json"
        try:
            content = await asyncio.to_thread(path.read_text, "utf-8")
            data = json.loads(content)
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    @staticmethod
    def _resolve(
        data: dict[str, Any], key: str, kwargs: dict[str, object]
    ) -> str:
        value: Any = data
        for part in key.split("."):
            if not isinstance(value, dict):
                return key
            value = value.get(part)
        if not isinstance(value, str):
            return key
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            return value

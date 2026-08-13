"""Application service for translating Verisure alarm messages to status data."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

AlarmStatus = dict[str, Any]
AlarmStatusConfig = Mapping[str, Any]


class AlarmStatusService:
    """Load alarm message configuration and build normalized status values."""

    def __init__(
        self,
        config_path: str | Path,
        *,
        read_config: Callable[[str], AlarmStatusConfig] | None = None,
    ) -> None:
        self._config_path = str(config_path)
        self._read_config = read_config or self._read_json
        self._config_cache: AlarmStatusConfig | None = None

    async def process_message(self, message: str) -> AlarmStatus:
        """Translate one provider message into the public alarm status shape."""
        if not message:
            return self.default_status()

        config = await self._load_config()
        response = self.default_status()
        self._apply_internal_matches(config, message, response)
        self._apply_external_matches(config, message, response)
        return response

    async def load_config(self) -> AlarmStatusConfig:
        """Load and cache configuration without blocking the event loop."""
        return await self._load_config()

    @staticmethod
    def default_status() -> AlarmStatus:
        """Return a status with every alarm category inactive."""
        return {
            "internal": {
                "day": {"status": False},
                "night": {"status": False},
                "total": {"status": False},
            },
            "external": {"status": False},
        }

    async def _load_config(self) -> AlarmStatusConfig:
        if self._config_cache is not None:
            return self._config_cache

        try:
            self._config_cache = await asyncio.to_thread(
                self._read_config, self._config_path
            )
        except (OSError, json.JSONDecodeError):
            self._config_cache = self._fallback_config()
        return self._config_cache

    @staticmethod
    def _read_json(config_path: str) -> AlarmStatusConfig:
        with open(config_path, encoding="utf-8") as config_file:
            value = json.load(config_file)
        if not isinstance(value, Mapping):
            raise json.JSONDecodeError("Configuration must be an object", "", 0)
        return value

    @staticmethod
    def _fallback_config() -> AlarmStatusConfig:
        return {
            "internal": {
                "day": {"alarm": []},
                "night": {"alarm": []},
                "total": {"alarm": []},
            },
            "external": {"alarm": []},
        }

    @staticmethod
    def _apply_internal_matches(
        config: AlarmStatusConfig,
        message: str,
        response: AlarmStatus,
    ) -> None:
        internal = config.get("internal", {})
        if not isinstance(internal, Mapping):
            return
        for subsection in ("day", "night", "total"):
            section = internal.get(subsection, {})
            if isinstance(section, Mapping) and message in section.get("alarm", []):
                response["internal"][subsection]["status"] = True

    @staticmethod
    def _apply_external_matches(
        config: AlarmStatusConfig,
        message: str,
        response: AlarmStatus,
    ) -> None:
        external = config.get("external", {})
        if isinstance(external, Mapping) and message in external.get("alarm", []):
            response["external"]["status"] = True

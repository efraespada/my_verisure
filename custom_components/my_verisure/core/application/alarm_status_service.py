"""Application service for translating Verisure alarm messages to status data."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

AlarmStatus = dict[str, Any]
AlarmStatusConfig = Mapping[str, Any]
KNOWN_PANEL_CODES = frozenset({"D", "E", "Q", "C"})


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
        internal_modes = response["internal"].values()
        inactive_messages = config.get("inactive", [])
        recognized = (
            any(mode["status"] is True for mode in internal_modes)
            or response["external"]["status"] is True
            or (isinstance(inactive_messages, list) and message in inactive_messages)
        )
        if recognized:
            # Each recognized message describes the complete zone combination.
            # Preserve unknown for unrecognized messages or missing configuration.
            for mode in (*response["internal"].values(), response["external"]):
                if mode["status"] is None:
                    mode["status"] = False
        return response

    async def load_config(self) -> AlarmStatusConfig:
        """Load and cache configuration without blocking the event loop."""
        return await self._load_config()

    @staticmethod
    def from_panel_code(code: str | None) -> AlarmStatus:
        """Translate complete panel codes verified against native responses.

        An accepted command alone is not evidence of a particular zone state.
        Unrecognized or missing confirmation remains unknown.
        """
        status = AlarmStatusService.default_status()
        if code not in KNOWN_PANEL_CODES:
            return status
        for mode in (*status["internal"].values(), status["external"]):
            mode["status"] = False
        status["external"]["status"] = code in ("E", "C")
        status["internal"]["night"]["status"] = code in ("Q", "C")
        return status

    @staticmethod
    def default_status() -> AlarmStatus:
        """Return a status with every alarm category unknown."""
        return {
            "internal": {
                "day": {"status": None},
                "night": {"status": None},
                "total": {"status": None},
            },
            "external": {"status": None},
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

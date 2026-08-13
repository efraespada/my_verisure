"""Persistence boundary for the coordinator's last snapshot."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..file_manager import FileManager

_LOGGER = logging.getLogger(__name__)
_SNAPSHOT_FILE = "coordinator_data.json"


class CoordinatorSnapshotStore:
    """Persist and inspect one entry-scoped coordinator snapshot."""

    def __init__(self, file_manager: FileManager) -> None:
        """Initialize the store with the entry-owned file manager."""
        self._file_manager = file_manager

    def load(self) -> dict[str, Any]:
        """Load a non-empty mapping or return an empty mapping."""
        try:
            payload = self._file_manager.load_json(_SNAPSHOT_FILE)
        except Exception as error:
            _LOGGER.error("Failed to load coordinator snapshot: %s", error)
            return {}
        if isinstance(payload, dict) and payload:
            return payload
        _LOGGER.warning("No coordinator snapshot found in %s", _SNAPSHOT_FILE)
        return {}

    async def save(self, payload: dict[str, Any]) -> bool:
        """Persist a snapshot without blocking the event loop."""
        try:
            return await self._file_manager.async_save_json(_SNAPSHOT_FILE, payload)
        except Exception as error:
            _LOGGER.error("Failed to save coordinator snapshot: %s", error)
            return False

    def metadata(self) -> dict[str, Any]:
        """Return bounded metadata for the persisted snapshot."""
        try:
            file_path = self._file_manager.get_file_path(_SNAPSHOT_FILE)
            exists = self._file_manager.file_exists(_SNAPSHOT_FILE)
            return {
                "file_path": str(file_path),
                "exists": exists,
                "file_size": self._file_manager.get_file_size(_SNAPSHOT_FILE),
                "last_modified": file_path.stat().st_mtime if exists else None,
            }
        except Exception as error:
            _LOGGER.error("Failed to inspect coordinator snapshot: %s", error)
            return {"error": str(error)}

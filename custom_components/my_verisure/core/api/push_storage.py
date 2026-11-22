"""Private atomic storage for entry-owned push/device state.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from ..file_manager import FileManager


class PrivatePushStore:
    def __init__(self, files: FileManager) -> None:
        self.files = files
        self._lock = asyncio.Lock()

    def _write(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".push-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(value, output)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    async def save(self, name: str, value: dict[str, Any]) -> None:
        path = self.files.get_file_path(name)
        async with self._lock:
            await asyncio.to_thread(self._write, path, value)

    async def load(self, name: str) -> dict[str, Any]:
        path = self.files.get_file_path(name)

        def read() -> dict[str, Any]:
            try:
                result = json.loads(path.read_text())
                return result if isinstance(result, dict) else {}
            except (OSError, ValueError):
                return {}
        return await asyncio.to_thread(read)

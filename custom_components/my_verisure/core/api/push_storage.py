"""Private atomic storage for entry-owned push/device state.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import contextvars
from collections.abc import Callable
from functools import partial
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
        self._replace_bytes(path, json.dumps(value).encode("utf-8"))

    def _replace_bytes(self, path: Path, value: bytes) -> None:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".push-")
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(value)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    async def save(self, name: str, value: dict[str, Any]) -> None:
        """Retain serialization until the executor write actually finishes."""
        path = self.files.get_file_path(name)
        async with self._lock:
            await self._run_owned(partial(self._write, path, value))

    def _restore_bytes(self, path: Path, value: bytes | None) -> None:
        if value is None:
            path.unlink(missing_ok=True)
        else:
            self._replace_bytes(path, value)

    async def restore_bytes(self, name: str, value: bytes | None) -> None:
        """Restore a private transaction snapshot, including prior absence."""
        if value is not None and not isinstance(value, bytes):
            raise TypeError("Private snapshot must contain bytes or no file")
        path = self.files.get_file_path(name)
        async with self._lock:
            await self._run_owned(partial(self._restore_bytes, path, value))

    async def _run_owned(self, operation: Callable[[], None]) -> None:
        """Caller retains the store lock until its executor operation finishes."""
        context = contextvars.copy_context()
        worker = asyncio.get_running_loop().run_in_executor(None, context.run, operation)
        cancelled = False
        while True:
            try:
                await asyncio.shield(worker)
                break
            except asyncio.CancelledError:
                # Cancelling an executor's awaiter does not stop its thread.
                # Keep a strong owner and the lock even on repeated cancel().
                cancelled = True
                if worker.done():
                    break
            except Exception:
                if not cancelled:
                    raise
                break
        if cancelled:
            if not worker.cancelled():
                worker.exception()
            raise asyncio.CancelledError
        worker.result()

    async def load(self, name: str) -> dict[str, Any]:
        path = self.files.get_file_path(name)

        def read() -> dict[str, Any]:
            try:
                result = json.loads(path.read_text())
                return result if isinstance(result, dict) else {}
            except (OSError, ValueError):
                return {}
        return await asyncio.to_thread(read)

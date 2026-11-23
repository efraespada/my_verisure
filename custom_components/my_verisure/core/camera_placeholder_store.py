"""Local atomic camera placeholders owned by an entry's filesystem adapter.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
import os
import re
import shutil
import threading
import time
import uuid

from PIL import Image

from .application.exceptions import MyVerisureError
from .application.models.camera_refresh import CameraRefresh
from .application.models.camera_refresh_data import CameraRefreshData
from .file_manager import FileManager


class LocalCameraPlaceholderStore:
    """Hide Pillow, directory layout and cancellation-safe file publication."""

    def __init__(
        self, files: FileManager, *, clock: Callable[[], float] = time.time
    ) -> None:
        self.files = files
        self._clock = clock
        self._lock = asyncio.Lock()

    async def ensure_placeholders(
        self, camera_identifiers: tuple[str, ...]
    ) -> CameraRefresh:
        """Drain the owned writer before returning or propagating cancellation."""
        if any(
            not isinstance(identifier, str)
            or re.fullmatch(r"(?:YP|YR)[0-9]{2,}", identifier) is None
            for identifier in camera_identifiers
        ):
            raise MyVerisureError("Invalid camera placeholder identifier")
        async with self._lock:
            stopped = threading.Event()
            worker = asyncio.create_task(
                asyncio.to_thread(
                    self._ensure_sync, tuple(dict.fromkeys(camera_identifiers)), stopped
                )
            )
            cancelled = False
            while True:
                try:
                    result = await asyncio.shield(worker)
                    break
                except asyncio.CancelledError:
                    cancelled = True
                    stopped.set()
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
            return result

    def _ensure_sync(
        self, identifiers: tuple[str, ...], stopped: threading.Event
    ) -> CameraRefresh:
        refresh_data: list[CameraRefreshData] = []
        timestamp = datetime.fromtimestamp(self._clock(), timezone.utc).astimezone()
        try:
            for identifier in identifiers:
                if stopped.is_set():
                    break
                camera_dir = self.files.get_file_path(f"cameras/{identifier}")
                if self._has_committed_images(camera_dir):
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=timestamp.isoformat(),
                            num_images=0,
                            camera_identifier=identifier,
                        )
                    )
                    continue
                destination = camera_dir / timestamp.strftime("%Y-%m-%d_%H-%M-%S")
                staging = camera_dir / f".{uuid.uuid4().hex}.staging"
                try:
                    staging.mkdir(parents=True)
                    self._write_images(staging)
                    if stopped.is_set():
                        break
                    staging.replace(destination)
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=timestamp.isoformat(),
                            num_images=4,
                            camera_identifier=identifier,
                        )
                    )
                finally:
                    if staging.exists():
                        shutil.rmtree(staging)
            return CameraRefresh(
                refresh_data=refresh_data,
                total_cameras=len(refresh_data),
                successful_refreshes=len(refresh_data),
                failed_refreshes=0,
                timestamp=timestamp.isoformat(),
            )
        except Exception:
            raise MyVerisureError("Dummy camera image creation failed") from None

    @staticmethod
    def _has_committed_images(camera_dir: Path) -> bool:
        if not camera_dir.exists():
            return False
        for directory in camera_dir.iterdir():
            if not directory.is_dir():
                continue
            marker = directory / ".complete"
            try:
                if marker.read_bytes() != b"complete":
                    continue
            except OSError:
                continue
            if any(
                file.is_file()
                and file.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif"}
                for file in directory.iterdir()
            ):
                return True
        return False

    @staticmethod
    def _write_images(directory: Path) -> None:
        with Image.new("RGB", (1920, 1080), color="black") as image:
            for name in ("1.jpg", "2.jpg", "3.jpg", "thumbnail.jpg"):
                image.save(directory / name, "JPEG", quality=85)
        with (directory / ".complete").open("wb") as marker:
            marker.write(b"complete")
            marker.flush()
            os.fsync(marker.fileno())

"""Verify local placeholder publication and executor ownership.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import threading
from unittest.mock import Mock

import pytest

from custom_components.my_verisure.core.application.camera_placeholders import (
    snapshot_camera_identifiers,
)
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.camera_placeholder_store import (
    LocalCameraPlaceholderStore,
)
from custom_components.my_verisure.core.file_manager import FileManager


@pytest.mark.asyncio
async def test_existing_committed_camera_image_is_preserved(tmp_path):
    camera = tmp_path / "data/cameras/YR01/2026-11-22_10-00-00"
    camera.mkdir(parents=True)
    (camera / "thumbnail.jpg").write_bytes(b"existing-real-image")
    (camera / ".complete").write_bytes(b"complete")
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    store._write_images = Mock(side_effect=AssertionError("Must preserve real images"))

    result = await store.ensure_placeholders(("YR01",))

    assert result.successful_refreshes == 1
    assert result.failed_refreshes == 0
    assert (camera / "thumbnail.jpg").read_bytes() == b"existing-real-image"
    store._write_images.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("fail_writer", [False, True])
async def test_cancelled_placeholder_writer_is_drained_before_cleanup(
    tmp_path, fail_writer
):
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    started, release, finished = threading.Event(), threading.Event(), threading.Event()

    def slow_writer(directory):
        started.set()
        if not release.wait(5):
            raise RuntimeError("test writer timed out")
        (directory / "thumbnail.jpg").write_bytes(b"partial-image")
        finished.set()
        if fail_writer:
            raise OSError("synthetic-sensitive")

    store._write_images = slow_writer
    task = asyncio.create_task(store.ensure_placeholders(("YR01",)))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        task.cancel()
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert finished.is_set()
        assert not list(tmp_path.rglob("*.staging"))
        assert not list(tmp_path.rglob("thumbnail.jpg"))
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_cancellation_before_writer_starts_creates_no_placeholder(tmp_path):
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    started, release = threading.Event(), threading.Event()
    original = store._ensure_sync

    def delayed_writer(identifiers, stopped):
        started.set()
        if not release.wait(5):
            raise RuntimeError("test writer timed out")
        return original(identifiers, stopped)

    store._ensure_sync = delayed_writer
    task = asyncio.create_task(store.ensure_placeholders(("YR01",)))
    try:
        assert await asyncio.to_thread(started.wait, 5)
        task.cancel()
        await asyncio.sleep(0)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not list(tmp_path.iterdir())
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)


@pytest.mark.asyncio
async def test_writer_cancellation_is_propagated_without_retaining_the_lock(tmp_path):
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    original = store._ensure_sync
    store._ensure_sync = Mock(side_effect=asyncio.CancelledError)

    with pytest.raises(asyncio.CancelledError):
        await asyncio.wait_for(store.ensure_placeholders(("YR01",)), timeout=2)

    store._ensure_sync = original
    result = await store.ensure_placeholders(())
    assert result.total_cameras == 0


@pytest.mark.asyncio
async def test_uncommitted_or_empty_directories_do_not_hide_placeholder(tmp_path):
    camera = tmp_path / "data/cameras/YR01"
    camera.mkdir(parents=True)
    (camera / "unrelated.txt").write_text("ignored")
    cases = [("missing", None), ("invalid", b"bad"), ("empty", b"complete")]
    for name, marker in cases:
        directory = camera / name
        directory.mkdir()
        if marker is not None:
            (directory / ".complete").write_bytes(marker)
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))

    result = await store.ensure_placeholders(("YR01",))

    assert result.successful_refreshes == 1
    assert len(list(camera.rglob("thumbnail.jpg"))) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("identifier", ["../YR01", "YR-1", "DOOR01", "YR1", ""])
async def test_placeholder_identifiers_cannot_escape_camera_directory(
    tmp_path, identifier
):
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    with pytest.raises(MyVerisureError, match="Invalid camera placeholder identifier"):
        await store.ensure_placeholders((identifier,))
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("devices", [None, {}, "bad", [None, {}, {"type": {}}]])
def test_snapshot_camera_selection_ignores_invalid_shapes(devices):
    assert (
        snapshot_camera_identifiers(
            {"detailed_installation": {"installation": {"devices": devices}}}
        )
        == ()
    )


@pytest.mark.parametrize(
    "snapshot",
    [
        {"detailed_installation": None},
        {"detailed_installation": {"installation": []}},
    ],
)
def test_snapshot_camera_selection_rejects_invalid_installation(snapshot):
    assert snapshot_camera_identifiers(snapshot) == ()


def test_snapshot_camera_selection_validates_codes_and_deduplicates_cameras():
    codes = [True, None, 1.5, "bad", "-1", "01", 1]
    devices = [{"type": "YR", "code": code, "is_active": True} for code in codes]
    assert snapshot_camera_identifiers(
        {"detailed_installation": {"installation": {"devices": devices}}}
    ) == ("YR01",)

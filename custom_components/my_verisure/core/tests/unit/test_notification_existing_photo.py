"""Retrieve an already-created photo signal without asking for another capture.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from datetime import datetime
import time
import threading
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo

import pytest

from custom_components.my_verisure.core.tests.image_fixtures import synthetic_jpeg_base64

from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.application.camera_image_storage import (
    CameraImageStorageResult,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def client(tmp_path):
    files = FileManager(tmp_path)
    value = CameraClient(SessionManager(file_manager=files), files)
    value._get_current_credentials = Mock(
        return_value=("synthetic", {"user": "synthetic"})
    )
    value.request_image = AsyncMock(
        side_effect=AssertionError("never capture a new image")
    )
    return value


def thumbnail(*, camera="YR07", signal="123", timestamp=None, signal_type="16"):
    return {
        "data": {
            "xSGetThumbnail": {
                "deviceCode": camera,
                "idSignal": signal,
                "signalType": signal_type,
                "timestamp": timestamp
                or datetime.fromtimestamp(
                    time.time(), ZoneInfo("Europe/Madrid")
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "deviceAlias": "synthetic",
                "image": synthetic_jpeg_base64(),
            }
        }
    }


async def test_external_photo_commits_exact_signal_with_two_read_queries(tmp_path):
    value = client(tmp_path)
    value._execute_query_direct = AsyncMock(
        side_effect=[
            thumbnail(),
            {
                "data": {
                    "xSGetPhotoImages": {
                        "devices": [
                            {
                                "code": "7",
                                "images": [
                                    {
                                        "id": str(i),
                                        "image": synthetic_jpeg_base64(),
                                    }
                                    for i in range(3)
                                ],
                            }
                        ]
                    },
                }
            },
        ]
    )
    result = await value.get_existing_photo(
        "house",
        "panel",
        "caps",
        signal_id="123",
        expected_camera_codes=("YR07",),
        event_timestamp=time.time(),
    )
    assert result["success"] and result["images_saved"] == 3
    assert result["camera_identifier"] == "YR07"
    assert value._execute_query_direct.await_count == 2
    assert all(
        "mutation" not in call.args[0]
        for call in value._execute_query_direct.await_args_list
    )
    assert all(
        call.args[1]["idSignal"] == "123"
        for call in value._execute_query_direct.await_args_list
    )
    assert (tmp_path / "data/cameras/YR07").exists()
    value.request_image.assert_not_awaited()


@pytest.mark.parametrize(
    "metadata",
    [
        thumbnail(camera="YR08"),
        thumbnail(camera="VR07"),
        thumbnail(camera={}),
        thumbnail(signal="other"),
        thumbnail(timestamp="2020-01-01 12:00:00"),
        thumbnail(timestamp="not-a-time"),
        thumbnail(signal_type="14"),
        {},
    ],
)
async def test_external_photo_unknown_metadata_never_fetches_or_saves_images(
    tmp_path, metadata
):
    value = client(tmp_path)
    value._execute_query_direct = AsyncMock(return_value=metadata)
    value.get_images = AsyncMock(
        side_effect=AssertionError("no image fetch for rejected thumbnail")
    )
    assert (
        await value.get_existing_photo(
            "house",
            "panel",
            "caps",
            signal_id="123",
            expected_camera_codes=("YR07",),
            event_timestamp=time.time(),
        )
        is None
    )
    assert value._execute_query_direct.await_count == 1
    value.get_images.assert_not_awaited()
    value.request_image.assert_not_awaited()


@pytest.mark.parametrize(
    "timestamp", [None, float("nan"), float("inf"), True, 1, time.time() + 120]
)
async def test_missing_stale_or_future_notification_time_prevents_queries(
    tmp_path, timestamp
):
    value = client(tmp_path)
    value._execute_query_direct = AsyncMock(
        side_effect=AssertionError("no provider reads")
    )
    assert (
        await value.get_existing_photo(
            "house",
            "panel",
            "caps",
            signal_id="123",
            expected_camera_codes=("YR07",),
            event_timestamp=timestamp,
        )
        is None
    )
    value._execute_query_direct.assert_not_awaited()


async def test_photo_persist_failure_never_returns_confirmed_result(tmp_path):
    value = client(tmp_path)
    value._execute_query_direct = AsyncMock(return_value=thumbnail())
    value.get_images = AsyncMock(return_value={"success": False, "images_saved": 1})
    assert (
        await value.get_existing_photo(
            "house",
            "panel",
            "caps",
            signal_id="123",
            expected_camera_codes=("YR07",),
            event_timestamp=time.time(),
        )
        is None
    )
    assert value._push_thumbnails == {}


@pytest.mark.parametrize("cancel_times", [1, 2])
async def test_cancelled_image_write_is_drained_before_operation_finishes(
    tmp_path, cancel_times
):
    value = client(tmp_path)
    value._execute_query_direct = AsyncMock(
        side_effect=[
            thumbnail(),
            {
                "data": {
                    "xSGetPhotoImages": {
                        "devices": [
                            {
                                "code": "7",
                                "images": [{"id": "0", "image": "c3ludGhldGlj"}],
                            }
                        ]
                    },
                }
            },
        ]
    )
    entered = asyncio.Event()
    release, finished = threading.Event(), threading.Event()
    loop = asyncio.get_running_loop()

    def slow_save(*args, **kwargs):
        loop.call_soon_threadsafe(entered.set)
        release.wait()
        finished.set()
        return CameraImageStorageResult(True, 1, 1, True)

    value._image_storage.save = Mock(side_effect=slow_save)
    pending = asyncio.create_task(
        value.get_existing_photo(
            "house",
            "panel",
            "caps",
            signal_id="123",
            expected_camera_codes=("YR07",),
            event_timestamp=time.time(),
        )
    )
    await entered.wait()
    try:
        for _ in range(cancel_times):
            pending.cancel()
            await asyncio.sleep(0)
            assert not pending.done()
        assert not finished.is_set()
    finally:
        release.set()
        await asyncio.gather(pending, return_exceptions=True)
    assert pending.cancelled()
    assert finished.is_set()
    assert value._push_thumbnails == {}

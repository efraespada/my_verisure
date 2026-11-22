"""Verify push completion through the camera adapter and polling fallback.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import base64
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.application.photo_notifications import PhotoNotifications
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.exceptions import MyVerisureServiceBlockedError
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def _setup(tmp_path):
    files = FileManager(tmp_path)
    session = SessionManager(file_manager=files)
    session.hash_token, session.username, session.password = "hash", "user", "password"
    broker = PhotoNotifications()
    client = CameraClient(session, files, notifications=broker)
    return client, broker


def _hint():
    return {"data": {"text": json.dumps({
        "request": "INF", "type": 0, "numinst": "house",
        "idSignal": "123", "timeStamp": int(time.time() * 1000),
    })}}


def _thumbnail(code="YR07"):
    return {"data": {"xSGetThumbnail": {
        "deviceCode": code, "idSignal": "123", "signalType": "16",
        "timestamp": datetime.fromtimestamp(time.time(), ZoneInfo("Europe/Madrid")).strftime("%Y-%m-%d %H:%M:%S"), "deviceAlias": "Entry",
        "image": base64.b64encode(b"synthetic-image").decode(),
    }}}


@pytest.mark.asyncio
async def test_push_confirms_exact_signal_and_downloads_without_extra_status(tmp_path, monkeypatch):
    client, broker = _setup(tmp_path)
    calls = []

    async def query(document, variables, headers):
        calls.append((document, variables))
        if "mutation RequestImages(" in document:
            return {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref"}}}
        if "query RequestImagesStatus(" in document:
            broker.receive(_hint(), "delivery")
            broker.receive(_hint(), "delivery")
            return {"data": {"xSRequestImagesStatus": {"res": "OK", "msg": "alarm-manager.photo-request.processing"}}}
        if "query mkGetThumbnail(" in document:
            assert variables == {"numinst": "house", "panel": "panel", "idSignal": "123"}
            return _thumbnail()
        assert "query mkGetPhotoImages(" in document
        assert variables["idSignal"] == "123"
        return {"data": {"xSGetPhotoImages": {"devices": [{
            "code": "7", "images": [{"id": str(i), "image": base64.b64encode(b"synthetic").decode()} for i in range(3)]
        }]}}}

    monkeypatch.setattr(client, "_execute_query_direct", query)
    result = await client.request_image("house", "panel", [7], "caps")
    assert result.success and result.signal_id == "123"
    images = await client.get_images("house", "panel", "YR", "YR07", "caps", signal_id=result.signal_id)
    assert images["success"] and images["images_saved"] == 3
    assert len(calls) == 4  # mutation, initial status, one thumbnail, photos
    assert client.last_completion_source == "push"
    assert broker._pending is None


@pytest.mark.asyncio
@pytest.mark.parametrize("wrong_camera", [False, True])
async def test_missing_or_wrong_camera_push_keeps_same_request_and_polling(tmp_path, monkeypatch, wrong_camera):
    client, broker = _setup(tmp_path)
    processing = {"data": {"xSRequestImagesStatus": {"res": "OK", "msg": "alarm-manager.photo-request.processing"}}}
    responses = [
        {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref"}}},
        processing,
    ]
    if wrong_camera:
        responses.append(_thumbnail("YR08"))
    responses.append({"data": {"xSRequestImagesStatus": {"res": "OK", "msg": "done"}}})
    transport = AsyncMock(side_effect=responses)
    monkeypatch.setattr(client, "_execute_query_direct", transport)
    wait = AsyncMock(return_value="123" if wrong_camera else None)
    monkeypatch.setattr(broker, "wait", wait)
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)
    result = await client.request_image("house", "panel", [7], "caps", max_attempts=2)
    assert result.success and result.signal_id is None
    assert client.last_completion_source == "polling"
    wait.assert_awaited_once_with(20)
    assert transport.await_count == (4 if wrong_camera else 3)
    assert transport.await_args_list[-1].args[1]["referenceId"] == "ref"
    if wrong_camera:
        assert 19 <= sleep.await_args.args[0] <= 20


@pytest.mark.asyncio
async def test_cancelling_photo_releases_pending_scope(tmp_path, monkeypatch):
    client, broker = _setup(tmp_path)
    monkeypatch.setattr(client, "_request_image", AsyncMock(side_effect=asyncio.CancelledError))
    with pytest.raises(asyncio.CancelledError):
        await client.request_image("house", "panel", [7], "caps")
    assert broker._pending is None


@pytest.mark.asyncio
async def test_full_photo_wrong_device_is_never_saved(tmp_path, monkeypatch):
    client, broker = _setup(tmp_path)
    transport = AsyncMock(side_effect=[_thumbnail(), {"data": {"xSGetPhotoImages": {"devices": [
        {"code": "8", "images": [{"id": "0", "image": "c3ludGhldGlj"}]}
    ]}}}])
    monkeypatch.setattr(client, "_execute_query_direct", transport)
    save = AsyncMock()
    monkeypatch.setattr(client._image_storage, "save", save)
    with pytest.raises(MyVerisureError, match="selected camera"):
        await client.get_images("house", "panel", "YR", "YR07", "caps", signal_id="123")
    save.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("timestamp", ["invalid", "2020-01-01 12:00:00"])
async def test_push_cannot_confirm_an_old_or_unparseable_thumbnail(tmp_path, monkeypatch, timestamp):
    client, broker = _setup(tmp_path)
    client._capture_started_at = time.time()
    value = _thumbnail()
    value["data"]["xSGetThumbnail"]["timestamp"] = timestamp
    monkeypatch.setattr(client, "_execute_query_direct", AsyncMock(return_value=value))
    assert await client._push_thumbnail("house", "panel", [7], {}, "123") is None
    assert client._push_thumbnails == {}


@pytest.mark.asyncio
async def test_provider_block_during_push_validation_propagates_without_retry(tmp_path, monkeypatch):
    client, broker = _setup(tmp_path)
    transport = AsyncMock(side_effect=[
        {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref"}}},
        {"data": {"xSRequestImagesStatus": {"res": "OK", "msg": "alarm-manager.photo-request.processing"}}},
        MyVerisureServiceBlockedError("synthetic provider block"),
    ])
    monkeypatch.setattr(client, "_execute_query_direct", transport)
    monkeypatch.setattr(broker, "wait", AsyncMock(return_value="123"))
    with pytest.raises(MyVerisureServiceBlockedError):
        await client.request_image("house", "panel", [7], "caps")
    assert transport.await_count == 3
    assert broker._pending is None

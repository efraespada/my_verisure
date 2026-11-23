"""Entry-owned push profile, event and private storage regressions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import json
import os
import time

import pytest

from custom_components.my_verisure.core.api.native_profile import ProfileContext
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.api.base_client import BaseClient
from custom_components.my_verisure.core.api.push_storage import PrivatePushStore
from custom_components.my_verisure.core.application.photo_notifications import PhotoNotifications
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def payload(installation="house", signal="123", timestamp=None):
    return {"data": {"text": json.dumps({
        "request": "INF", "type": 0, "numinst": installation,
        "idSignal": signal, "timeStamp": timestamp or int(time.time() * 1000),
    })}}


@pytest.mark.asyncio
async def test_push_profile_keeps_uuid_and_isolates_other_entry(tmp_path):
    context = ProfileContext()
    files = FileManager(tmp_path / "one")
    device = DeviceManager(files, context)
    other = DeviceManager(FileManager(tmp_path / "two"))
    await device.async_ensure_device_identifiers()
    await other.async_ensure_device_identifiers()
    before = device.get_device_identifiers()
    await device.async_set_push_token("synthetic-fcm-token")
    after = device.get_device_identifiers()
    assert after["uuid"] == before["uuid"]
    assert after["idDeviceIndigitall"] == before["idDeviceIndigitall"]
    assert after["idDevice"] == "synthetic-fcm-token"
    variables = device.get_login_variables(context.current.session_id)
    assert variables["callby"] == "OWA_10"
    assert variables["deviceOsVersion"] == "16"
    assert other.profile_context.current.callby == "OWI_10"
    client = BaseClient(SessionManager(file_manager=files), context)
    auth = json.loads(client._get_session_headers({"user": "synthetic"}, "token")["auth"])
    assert auth["callby"] == "OWA_10"
    assert auth["id"].startswith("OWA")
    restored = DeviceManager(files)
    await restored.async_ensure_device_identifiers()
    assert restored.profile_context.current.callby == "OWA_10"


@pytest.mark.asyncio
async def test_private_store_is_private_and_rejects_escape(tmp_path):
    store = PrivatePushStore(FileManager(tmp_path))
    await store.save("push.json", {"secret": "synthetic"})
    assert (tmp_path / "data/push.json").stat().st_mode & 0o777 == 0o600
    assert await store.load("push.json") == {"secret": "synthetic"}
    with pytest.raises(ValueError):
        await store.save("../../escape.json", {})


@pytest.mark.asyncio
async def test_private_store_failed_replace_preserves_old_bytes(tmp_path, monkeypatch):
    store = PrivatePushStore(FileManager(tmp_path))
    await store.save("push.json", {"version": 1})

    def fail(*args):
        raise OSError("synthetic write failure")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(OSError):
        await store.save("push.json", {"version": 2})
    assert await store.load("push.json") == {"version": 1}
    assert len(list((tmp_path / "data").iterdir())) == 1


@pytest.mark.asyncio
async def test_photo_broker_accepts_only_pending_matching_fresh_hints():
    broker = PhotoNotifications()
    broker.connected = True
    broker.begin("house", time.time())
    broker.receive(payload("other"), "foreign")
    broker.receive(payload(timestamp=1000), "stale")
    broker.receive({"data": {"text": "broken"}}, "malformed")
    assert await broker.wait(0.001) is None
    broker.receive(payload(), "delivery")
    assert await broker.wait(0.01) == "123"
    broker.receive(payload(), "delivery")
    assert await broker.wait(0.001) is None
    broker.finish()
    broker.receive(payload(signal="999"), "idle")
    broker.begin("house", time.time())
    assert await broker.wait(0.001) is None


@pytest.mark.asyncio
async def test_broker_overlap_and_unload_cancel_pending_wait():
    broker = PhotoNotifications()
    broker.begin("house", time.time())
    with pytest.raises(RuntimeError):
        broker.begin("house", time.time())
    pending = asyncio.create_task(broker.wait(10))
    await asyncio.sleep(0)
    broker.close()
    with pytest.raises(asyncio.CancelledError):
        await pending
    broker.finish()

"""Push decoding, persistence and SDK task ownership regressions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import base64
import json
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding, NoEncryption, PrivateFormat, PublicFormat,
)
from http_ece import encrypt
import pytest

from custom_components.my_verisure.core.api import push_receiver
from custom_components.my_verisure.core.api.push_decoder import decode
from custom_components.my_verisure.core.api.push_receiver import PushReceiver
from custom_components.my_verisure.core.application.photo_notifications import PhotoNotifications
from custom_components.my_verisure.core.file_manager import FileManager


class FakeClient:
    def __init__(self, callback, fcm_config, credentials, updated, **kwargs):
        self.callback = callback
        self.credentials = credentials or {
            "fcm": {"registration": {"token": "synthetic-registration-token"}},
            "keys": {"private": "synthetic", "public": "synthetic", "secret": "synthetic"},
            "gcm": {"android_id": "123", "security_token": "456", "app_id": "synthetic"},
            "config": {"project_id": push_receiver.PROJECT_ID},
        }
        self.updated = updated
        self.register = SimpleNamespace(close=AsyncMock())
        self.tasks = []
        self.stopping_lock = None
        self.started = False
        self.checkin_or_register = AsyncMock(side_effect=self.checkin)

    async def checkin(self):
        self.updated(self.credentials)
        return self.credentials["fcm"]["registration"]["token"]

    async def start(self):
        self.stopping_lock = asyncio.Lock()
        self.tasks = [asyncio.create_task(asyncio.Event().wait())]
        self.started = True

    async def stop(self):
        # Emulate the SDK's early return: the owner must cancel this task.
        self.started = False

    def is_started(self):
        return self.started


@pytest.mark.asyncio
async def test_receiver_persists_reuses_and_drains_sdk_on_unload(tmp_path):
    files = FileManager(tmp_path)
    broker = PhotoNotifications()
    receiver = PushReceiver(files, broker, client_factory=FakeClient)
    token = await receiver.async_prepare()
    client = receiver._client
    assert await receiver.async_prepare() == token
    client.checkin_or_register.assert_awaited_once()
    assert await receiver.async_start()
    assert broker.connected
    client.callback({"data": {"text": "{}"}}, "delivery", None)
    tasks = list(client.tasks)
    await receiver.async_stop()
    assert all(task.done() for task in tasks)
    assert not broker.connected
    assert receiver._runner is None
    stored = files.get_file_path("push_credentials.json")
    assert stored.stat().st_mode & 0o777 == 0o600
    assert "delivery" in json.loads(stored.read_text())["persistent_ids"]
    restored = PushReceiver(files, PhotoNotifications(), client_factory=FakeClient)
    assert await restored.async_prepare() == token
    restored._client.checkin_or_register.assert_not_awaited()
    assert restored.notifications.recent_ids == ["delivery"]
    await restored.async_stop()


@pytest.mark.asyncio
async def test_invalid_cached_credentials_need_normal_registration(tmp_path):
    receiver = PushReceiver(FileManager(tmp_path), PhotoNotifications(), client_factory=FakeClient)
    await receiver._store.save("push_credentials.json", {"credentials": {"config": {}}})
    # The SDK, not an incomplete saved record, supplies fresh credentials.
    class ReplacingClient(FakeClient):
        async def checkin(self):
            self.credentials = FakeClient(None, None, None, None).credentials
            return await super().checkin()
    receiver._factory = ReplacingClient
    assert await receiver.async_prepare() == "synthetic-registration-token"
    receiver._client.checkin_or_register.assert_awaited_once()
    await receiver.async_stop()


@pytest.mark.asyncio
async def test_mcs_rejection_marks_registration_for_recovery(monkeypatch):
    client = object.__new__(push_receiver.VerisureFcmClient)
    rejected = push_receiver.LoginResponse()
    rejected.error.code = 401
    parent = AsyncMock()
    monkeypatch.setattr(push_receiver.FcmPushClient, "_handle_message", parent)
    await client._handle_message(rejected)
    assert client.registration_invalid
    parent.assert_awaited_once_with(rejected)


@pytest.mark.asyncio
async def test_failed_private_write_prevents_binding_token(tmp_path, monkeypatch):
    receiver = PushReceiver(FileManager(tmp_path), PhotoNotifications(), client_factory=FakeClient)
    monkeypatch.setattr(receiver._store, "save", AsyncMock(side_effect=OSError("synthetic")))
    with pytest.raises(OSError, match="persisted"):
        await receiver.async_prepare()
    assert receiver._runner is None
    receiver._client.register.close.assert_awaited_once()
    await receiver.async_stop()


@pytest.mark.asyncio
async def test_cancelled_registration_closes_http_owner(tmp_path):
    receiver = PushReceiver(FileManager(tmp_path), PhotoNotifications(), client_factory=FakeClient)
    entered = asyncio.Event()

    async def block(client):
        entered.set()
        await asyncio.Event().wait()

    class BlockingClient(FakeClient):
        async def checkin(self):
            return await block(self)

    receiver._factory = BlockingClient
    task = asyncio.create_task(receiver.async_prepare())
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    receiver._client.register.close.assert_awaited_once()
    assert receiver.token is None
    await receiver.async_stop()


@pytest.mark.asyncio
async def test_failed_start_backoff_has_no_leaked_sdk_tasks(tmp_path):
    class BrokenClient(FakeClient):
        async def start(self):
            await super().start()
            raise OSError("synthetic connection failure")

    broker = PhotoNotifications()
    receiver = PushReceiver(FileManager(tmp_path), broker, client_factory=BrokenClient)
    await receiver.async_prepare()
    client = receiver._client
    assert not await receiver.async_start()
    await receiver.async_stop()
    assert not broker.connected
    assert all(task.done() for task in client.tasks)


def _b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


@pytest.mark.parametrize("reversed_keys", [False, True])
def test_authenticated_combined_header_and_tamper_rejection(reversed_keys):
    recipient = ec.generate_private_key(ec.SECP256R1())
    sender = ec.generate_private_key(ec.SECP256R1())
    def public(key):
        return key.public_key().public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)
    secret, salt = os.urandom(16), os.urandom(16)
    credentials = {"keys": {
        "private": _b64(recipient.private_bytes(Encoding.DER, PrivateFormat.PKCS8, NoEncryption())),
        "secret": _b64(secret),
    }}
    expected = {"data": {"text": "synthetic"}}
    encrypted = encrypt(json.dumps(expected).encode(), salt=salt, private_key=sender,
                        dh=public(recipient), auth_secret=secret, version="aesgcm")
    chunks = [f'p256ecdsa="{_b64(public(recipient))}"', f'dh="{_b64(public(sender))}"']
    if reversed_keys:
        chunks.reverse()
    record = {"envelope": {"raw_data": base64.b64encode(encrypted).decode(), "app_data": [
        {"key": "crypto-key", "value": "; ".join(chunks)},
        {"key": "encryption", "value": f'salt="{_b64(salt)}";rs=4096'},
    ]}}
    assert decode(record, credentials) == expected
    record["envelope"]["raw_data"] = base64.b64encode(encrypted[:-1] + bytes([encrypted[-1] ^ 1])).decode()
    with pytest.raises(Exception):
        decode(record, credentials)


def test_adapter_filters_sender_and_invalid_envelope_without_leaking(monkeypatch, caplog):
    client = object.__new__(push_receiver.VerisureFcmClient)
    client.credentials = {}
    client.callback_context = None
    delivered = []
    client.callback = lambda *args: delivered.append(args)
    message = SimpleNamespace(raw_data=b"encrypted", app_data=[], persistent_id="id")
    def decoder(*args):
        return {"from": "other-sender", "secret": "synthetic-sensitive"}
    monkeypatch.setattr(push_receiver, "decode", decoder)
    client._handle_data_message(message)
    assert delivered == []
    monkeypatch.setattr(push_receiver, "decode", lambda *args: {"from": push_receiver.MESSAGING_SENDER_ID})
    client._handle_data_message(message)
    assert len(delivered) == 1
    monkeypatch.setattr(push_receiver, "decode", lambda *args: (_ for _ in ()).throw(ValueError("synthetic-sensitive")))
    client._handle_data_message(message)
    assert "synthetic-sensitive" not in caplog.text

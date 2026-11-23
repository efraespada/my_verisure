"""Optional notification replay and token-change callback regressions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import copy
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api import push_receiver
from custom_components.my_verisure.core.api.push_receiver import PushReceiver
from custom_components.my_verisure.core.file_manager import FileManager

from .test_push_receiver import FakeClient


class ReplaySink:
    def __init__(self):
        self.connected = False
        self.ids = []
        self.replay = {"version": 1, "seen": [{"hash": "a" * 64, "time": 1000}]}
        self.restored = []
        self.closed = False

    @property
    def recent_ids(self):
        return list(self.ids)

    def restore_ids(self, ids):
        self.ids = list(ids)

    def export_replay(self):
        return self.replay

    def restore_replay(self, state):
        self.restored.append(copy.deepcopy(state))
        self.replay = copy.deepcopy(state)

    def receive(self, payload, persistent_id):
        self.ids.append(persistent_id)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def public_configuration(monkeypatch):
    resolver = AsyncMock(return_value="synthetic-public-client-key")
    monkeypatch.setattr(push_receiver, "async_resolve_public_api_key", resolver)
    return resolver


@pytest.mark.asyncio
async def test_generic_sink_replay_is_private_and_restored_without_http(
    tmp_path, public_configuration
):
    files = FileManager(tmp_path)
    sink = ReplaySink()
    receiver = PushReceiver(files, sink, client_factory=FakeClient)
    token = await receiver.async_prepare()
    stored = await receiver._store.load("push_credentials.json")
    assert stored["notification_replay"] == sink.replay
    assert files.get_file_path("push_credentials.json").stat().st_mode & 0o777 == 0o600
    await receiver.async_stop()

    public_configuration.reset_mock()
    restored_sink = ReplaySink()
    restored = PushReceiver(files, restored_sink, client_factory=FakeClient)
    assert await restored.async_prepare() == token
    assert restored_sink.restored == [stored["notification_replay"]]
    public_configuration.assert_not_awaited()
    await restored.async_stop()


@pytest.mark.asyncio
async def test_sdk_resume_ids_are_valid_and_bounded_for_generic_sinks(tmp_path):
    sink = ReplaySink()
    receiver = PushReceiver(FileManager(tmp_path), sink, client_factory=FakeClient)
    await receiver.async_prepare()
    sink.ids = [f"delivery-{i}" for i in range(256)] + ["", None, "x" * 513]
    supplied = []

    def factory(*args, **kwargs):
        supplied.append(kwargs["received_persistent_ids"])
        return FakeClient(*args, **kwargs)

    receiver._factory = factory
    receiver._new_client()
    assert supplied == [[f"delivery-{i}" for i in range(128, 256)]]
    receiver._received({}, "new-delivery", None)
    await receiver._writer
    stored = await receiver._store.load("push_credentials.json")
    assert len(stored["persistent_ids"]) == 128
    assert stored["persistent_ids"][-1] == "new-delivery"
    await receiver.async_stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid", [[], {"seen": "x" * (128 * 1024 + 1)}, {"time": float("nan")}]
)
async def test_invalid_export_cannot_claim_durable_registration(tmp_path, invalid):
    sink = ReplaySink()
    sink.replay = invalid
    receiver = PushReceiver(FileManager(tmp_path), sink, client_factory=FakeClient)
    with pytest.raises(OSError, match="persisted"):
        await receiver.async_prepare()
    await receiver.async_stop()


@pytest.mark.asyncio
async def test_invalid_optional_restore_keeps_cached_transport_and_legacy_ids(
    tmp_path, public_configuration
):
    files = FileManager(tmp_path)
    initial = PushReceiver(files, ReplaySink(), client_factory=FakeClient)
    token = await initial.async_prepare()
    value = await initial._store.load("push_credentials.json")
    value.update(
        notification_replay=["invalid"], persistent_ids=["valid", "", "x" * 513]
    )
    await initial._store.save("push_credentials.json", value)
    await initial.async_stop()

    public_configuration.reset_mock()
    sink = ReplaySink()
    restored = PushReceiver(files, sink, client_factory=FakeClient)
    assert await restored.async_prepare() == token
    assert sink.restored == []
    assert sink.ids == ["valid"]
    public_configuration.assert_not_awaited()
    await restored.async_stop()


@pytest.mark.asyncio
async def test_token_change_callback_is_sync_once_per_value_and_ignored_after_close(
    tmp_path,
):
    changes = []
    receiver = PushReceiver(
        FileManager(tmp_path),
        ReplaySink(),
        client_factory=FakeClient,
        on_token_changed=changes.append,
    )
    token = await receiver.async_prepare()
    assert changes == [token]
    receiver._credentials_updated(copy.deepcopy(receiver._credentials))
    assert changes == [token]
    rotated = copy.deepcopy(receiver._credentials)
    rotated["fcm"]["registration"]["token"] = "synthetic-rotated-token"
    receiver._credentials_updated(rotated)
    assert changes == [token, "synthetic-rotated-token"]
    await receiver.async_stop()
    writer = receiver._writer
    rotated["fcm"]["registration"]["token"] = "synthetic-late-token"
    receiver._credentials_updated(rotated)
    assert changes == [token, "synthetic-rotated-token"]
    assert receiver._writer is writer


@pytest.mark.asyncio
async def test_token_callback_failure_does_not_lose_receiver_state_or_leak(
    tmp_path, caplog
):
    def fail(token):
        raise ValueError("synthetic-private-callback-value")

    receiver = PushReceiver(
        FileManager(tmp_path),
        ReplaySink(),
        client_factory=FakeClient,
        on_token_changed=fail,
    )
    assert await receiver.async_prepare() == "synthetic-registration-token"
    assert "synthetic-private-callback-value" not in caplog.text
    assert (await receiver._store.load("push_credentials.json"))[
        "credentials"
    ] == receiver._credentials
    await receiver.async_stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", [None, False, "short"])
async def test_invalid_sdk_token_does_not_replace_working_state(tmp_path, invalid):
    changes = []
    receiver = PushReceiver(
        FileManager(tmp_path),
        ReplaySink(),
        client_factory=FakeClient,
        on_token_changed=changes.append,
    )
    token = await receiver.async_prepare()
    previous = copy.deepcopy(receiver._credentials)
    changed = copy.deepcopy(previous)
    changed["fcm"]["registration"]["token"] = invalid
    with pytest.raises(ValueError):
        receiver._credentials_updated(changed)
    assert receiver._credentials == previous
    assert receiver.token == token
    assert changes == [token]
    await receiver.async_stop()

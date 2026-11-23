"""Offline recovery and MCS frame budget regressions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from threading import Event
from types import SimpleNamespace

from firebase_messaging.proto.mcs_pb2 import HeartbeatPing
import pytest

from custom_components.my_verisure.core.api.push_receiver import VerisureFcmClient
from custom_components.my_verisure.core.api.push_storage import PrivatePushStore
from custom_components.my_verisure.core.file_manager import FileManager


async def checkpoint():
    ready = asyncio.Event()
    asyncio.get_running_loop().call_soon(ready.set)
    await ready.wait()


@pytest.mark.asyncio
async def test_cancelled_write_retains_order_until_its_thread_finishes(
    tmp_path, monkeypatch
):
    store = PrivatePushStore(FileManager(tmp_path))
    original = store._write
    entered, release, finished, newer_entered = Event(), Event(), Event(), Event()

    def write(path, value):
        if value["version"] == 1:
            entered.set()
            try:
                assert release.wait(5), "Older thread was never released"
                original(path, value)
            finally:
                finished.set()
        else:
            newer_entered.set()
            original(path, value)

    monkeypatch.setattr(store, "_write", write)
    older = asyncio.create_task(store.save("push.json", {"version": 1}))
    newer = None
    try:
        assert await asyncio.to_thread(entered.wait, 3)
        older.cancel()
        await checkpoint()
        assert not older.done()
        newer = asyncio.create_task(store.save("push.json", {"version": 2}))
        await checkpoint()
        assert not newer_entered.is_set()
        # A second cancellation must not release ownership of the old thread.
        older.cancel()
        await checkpoint()
        assert not older.done()
        assert not newer_entered.is_set()
        release.set()
        result = await asyncio.gather(older, newer, return_exceptions=True)
        assert isinstance(result[0], asyncio.CancelledError)
        assert result[1] is None
        assert finished.is_set()
        assert (await store.load("push.json"))["version"] == 2
    finally:
        release.set()
        assert await asyncio.to_thread(finished.wait, 5)
        await asyncio.gather(
            *(task for task in (older, newer) if task), return_exceptions=True
        )


class RecordingReader:
    def __init__(self, data):
        self.data = data
        self.requests = []

    async def readexactly(self, count):
        self.requests.append(count)
        if len(self.data) < count:
            raise asyncio.IncompleteReadError(self.data, count)
        result, self.data = self.data[:count], self.data[count:]
        return result


def client_with_reader(data):
    client = object.__new__(VerisureFcmClient)
    client.first_message = False
    client.reader = RecordingReader(data)
    client.config = SimpleNamespace(log_debug_verbose=False)
    return client


@pytest.mark.asyncio
async def test_oversized_mcs_frame_is_rejected_before_body_read():
    frame_length = VerisureFcmClient._encode_varint32(256 * 1024 + 1)
    client = client_with_reader(b"\x00" + frame_length)
    with pytest.raises(ValueError, match="frame"):
        await client._receive_msg()
    assert all(count == 1 for count in client.reader.requests)


@pytest.mark.asyncio
async def test_overlong_mcs_length_stops_after_five_bytes():
    client = client_with_reader(b"\x80" * 6 + b"\x00")
    with pytest.raises(ValueError, match="frame"):
        await client._read_varint32()
    assert len(client.reader.requests) == 5


@pytest.mark.asyncio
async def test_empty_heartbeat_frame_remains_supported():
    client = client_with_reader(b"\x00\x00")
    assert isinstance(await client._receive_msg(), HeartbeatPing)


@pytest.mark.asyncio
@pytest.mark.parametrize("length", [0, 65536, 256 * 1024])
async def test_valid_mcs_length_boundaries_remain_supported(length):
    client = client_with_reader(VerisureFcmClient._encode_varint32(length))
    assert await client._read_varint32() == length

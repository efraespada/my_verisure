"""Device-address staging, byte-exact rollback and private binding states.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from threading import Event

import pytest

from custom_components.my_verisure.core.api import device_manager
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.api.push_storage import PrivatePushStore
from custom_components.my_verisure.core.file_manager import FileManager


@pytest.fixture
async def device(tmp_path, monkeypatch):
    identifiers = {
        "idDevice": "synthetic-previous-device-token",
        "uuid": "synthetic-stable-uuid",
        "idDeviceIndigitall": "synthetic-separate-provider-id",
        "deviceName": "Synthetic receiver",
        "deviceBrand": "HomeAssistant",
        "deviceOsVersion": "16",
        "deviceVersion": "synthetic-1",
    }
    monkeypatch.setattr(
        DeviceManager, "_generate_device_identifiers", lambda self: dict(identifiers)
    )
    manager = DeviceManager(FileManager(tmp_path))
    await manager.async_ensure_device_identifiers()
    path = manager._resolve_file_manager().get_file_path("device_identifiers.json")
    path.write_bytes(b" \n" + path.read_bytes() + b"\n")
    return manager


async def checkpoint():
    ready = asyncio.Event()
    asyncio.get_running_loop().call_soon(ready.set)
    await ready.wait()


@pytest.mark.asyncio
async def test_stage_is_memory_only_and_rollback_restores_identity_and_exact_bytes(
    device,
):
    path = device._resolve_file_manager().get_file_path("device_identifiers.json")
    before, original = path.read_bytes(), device.get_device_identifiers()
    profile = device.profile_context.current
    stage, changed = await device.async_stage_push_token("synthetic-candidate-token")
    assert changed
    assert path.read_bytes() == before
    candidate = device.get_device_identifiers()
    assert candidate["idDevice"] == "synthetic-candidate-token"
    assert candidate["uuid"] == original["uuid"]
    assert candidate["idDeviceIndigitall"] == original["idDeviceIndigitall"]
    assert device.profile_context.current.callby == "OWA_10"
    assert "synthetic-candidate-token" not in repr(stage)
    await device.async_rollback_staged_push_token(stage)
    assert device.get_device_identifiers() == original
    assert device.profile_context.current == profile
    assert path.read_bytes() == before
    await device.async_rollback_staged_push_token(stage)
    assert path.read_bytes() == before


@pytest.mark.asyncio
async def test_successful_commit_is_durable_and_keeps_stable_uuid(device):
    original = device.get_device_identifiers()
    stage, changed = await device.async_stage_push_token("synthetic-accepted-token")
    assert changed
    await device.async_commit_staged_push_token(stage)
    path = device._resolve_file_manager().get_file_path("device_identifiers.json")
    assert path.stat().st_mode & 0o777 == 0o600
    restored = DeviceManager(device._resolve_file_manager())
    await restored.async_ensure_device_identifiers()
    assert restored.get_device_identifiers()["idDevice"] == "synthetic-accepted-token"
    assert restored.get_device_identifiers()["uuid"] == original["uuid"]
    assert restored.profile_context.current.callby == "OWA_10"


@pytest.mark.asyncio
async def test_unchanged_stage_commits_without_rewriting_file(device, monkeypatch):
    await device.async_set_push_token("synthetic-same-token")
    path = device._resolve_file_manager().get_file_path("device_identifiers.json")
    before = path.read_bytes()

    def forbidden_write(*args):
        raise AssertionError("Unchanged binding must not write")

    stage, changed = await device.async_stage_push_token("synthetic-same-token")
    assert not changed
    monkeypatch.setattr(device._binding_store, "_write", forbidden_write)
    await device.async_commit_staged_push_token(stage)
    assert path.read_bytes() == before


@pytest.mark.asyncio
@pytest.mark.parametrize("token", [None, False, "short", "x" * 4097])
async def test_invalid_candidate_does_not_change_existing_state(device, token):
    original = device.get_device_identifiers()
    with pytest.raises(ValueError):
        await device.async_stage_push_token(token)
    assert device.get_device_identifiers() == original


@pytest.mark.asyncio
async def test_overlapping_stage_and_stale_snapshot_are_rejected(device):
    first, _ = await device.async_stage_push_token("synthetic-first-token")
    with pytest.raises(RuntimeError):
        await device.async_stage_push_token("synthetic-overlapping-token")
    with pytest.raises(RuntimeError):
        await device.async_set_push_token("synthetic-legacy-overlap-token")
    await device.async_rollback_staged_push_token(first)
    second, _ = await device.async_stage_push_token("synthetic-second-token")
    with pytest.raises(ValueError):
        await device.async_rollback_staged_push_token(first)
    with pytest.raises(ValueError):
        await device.async_commit_staged_push_token(first)
    await device.async_commit_staged_push_token(second)
    assert device.get_device_identifiers()["idDevice"] == "synthetic-second-token"


@pytest.mark.asyncio
async def test_failed_commit_rolls_back_memory_profile_and_original_file(
    device, monkeypatch
):
    path = device._resolve_file_manager().get_file_path("device_identifiers.json")
    before, original = path.read_bytes(), device.get_device_identifiers()
    profile = device.profile_context.current
    stage, _ = await device.async_stage_push_token("synthetic-failed-token")

    def fail(*args):
        raise OSError("Synthetic write failure")

    monkeypatch.setattr(device._binding_store, "_write", fail)
    with pytest.raises(OSError):
        await device.async_commit_staged_push_token(stage)
    assert path.read_bytes() == before
    assert device.get_device_identifiers() == original
    assert device.profile_context.current == profile
    await device.async_rollback_staged_push_token(stage)


@pytest.mark.asyncio
async def test_cancelled_commit_drains_write_then_restores_previous_identity(
    device, monkeypatch
):
    path = device._resolve_file_manager().get_file_path("device_identifiers.json")
    before, original = path.read_bytes(), device.get_device_identifiers()
    profile = device.profile_context.current
    stage, _ = await device.async_stage_push_token("synthetic-cancelled-token")
    write = device._binding_store._write
    entered, release, finished = Event(), Event(), Event()

    def delayed(*args):
        entered.set()
        try:
            assert release.wait(5)
            write(*args)
        finally:
            finished.set()

    monkeypatch.setattr(device._binding_store, "_write", delayed)
    committing = asyncio.create_task(device.async_commit_staged_push_token(stage))
    try:
        assert await asyncio.to_thread(entered.wait, 3)
        committing.cancel()
        await checkpoint()
        committing.cancel()
        await checkpoint()
        assert not committing.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await committing
        assert finished.is_set()
        assert path.read_bytes() == before
        assert device.get_device_identifiers() == original
        assert device.profile_context.current == profile
    finally:
        release.set()
        await asyncio.gather(committing, return_exceptions=True)


@pytest.mark.asyncio
async def test_cancelled_rollback_drains_its_owned_restore(device, monkeypatch):
    path = device._resolve_file_manager().get_file_path("device_identifiers.json")
    before, original = path.read_bytes(), device.get_device_identifiers()
    stage, _ = await device.async_stage_push_token("synthetic-candidate-token")
    restore = device._binding_store._restore_bytes
    entered, release = Event(), Event()

    def delayed(*args):
        entered.set()
        assert release.wait(5)
        restore(*args)

    monkeypatch.setattr(device._binding_store, "_restore_bytes", delayed)
    rolling_back = asyncio.create_task(device.async_rollback_staged_push_token(stage))
    try:
        assert await asyncio.to_thread(entered.wait, 3)
        rolling_back.cancel()
        await checkpoint()
        assert not rolling_back.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await rolling_back
        assert path.read_bytes() == before
        assert device.get_device_identifiers() == original
    finally:
        release.set()
        await asyncio.gather(rolling_back, return_exceptions=True)


@pytest.mark.asyncio
async def test_private_byte_restore_preserves_bytes_and_can_restore_missing_file(
    tmp_path,
):
    files = FileManager(tmp_path)
    store = PrivatePushStore(files)
    original = b'{\n  "value": "synthetic"\n}\n'
    await store.restore_bytes("synthetic.json", original)
    path = files.get_file_path("synthetic.json")
    assert path.read_bytes() == original
    assert path.stat().st_mode & 0o777 == 0o600
    await store.restore_bytes("synthetic.json", None)
    assert not path.exists()


def test_public_binding_states_have_safe_stable_values():
    assert {state.value for state in device_manager.PushBindingState} == {
        "disabled",
        "pending",
        "bound",
        "reauth_required",
        "degraded",
    }

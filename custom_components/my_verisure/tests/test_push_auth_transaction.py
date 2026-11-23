"""Verify native push binding transactions using only local persistence.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure import push
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager

pytestmark = [pytest.mark.homeassistant, pytest.mark.asyncio]


async def file_bytes(path):
    return await asyncio.to_thread(Path(path).read_bytes)


@pytest.fixture
async def binding(hass, tmp_path, monkeypatch):
    root = build_my_verisure_composition_root(project_root=tmp_path, push_enabled=True)
    device, session = root.get(DeviceManager), root.get(SessionManager)
    await device.async_ensure_device_identifiers()
    session.hash_token, session.refresh_token = (
        "synthetic-ios-access",
        "synthetic-ios-refresh",
    )
    session.current_installation = {"number": "synthetic-house"}
    await session.async_persist_session_to_disk()
    device_path = root.get(FileManager).get_file_path("device_identifiers.json")
    initial_device, initial_session = (
        await file_bytes(device_path),
        await file_bytes(session.session_file),
    )
    initial_identifiers = device.get_device_identifiers()
    receiver = SimpleNamespace(
        async_prepare=AsyncMock(return_value="synthetic-fcm-address"),
        async_start=AsyncMock(),
        async_stop=AsyncMock(),
        diagnostics=Mock(return_value={}),
        request_state_save=Mock(),
    )
    receiver_options = {}

    def construct(*args, **kwargs):
        receiver_options.update(kwargs)
        return receiver

    monkeypatch.setattr(push, "PushReceiver", construct)
    adapter = push.HomeAssistantPush(
        hass, root, installation_id="synthetic-house", entry_id="synthetic-entry"
    )
    value = SimpleNamespace(
        adapter=adapter,
        root=root,
        device=device,
        session=session,
        receiver=receiver,
        options=receiver_options,
        device_path=device_path,
        initial_device=initial_device,
        initial_session=initial_session,
        initial_identifiers=initial_identifiers,
    )
    yield value
    await adapter.async_stop()


async def assert_restored(value):
    assert value.device.get_device_identifiers() == value.initial_identifiers
    assert value.device.profile_context.current.callby == "OWI_10"
    assert value.session.hash_token == "synthetic-ios-access"
    assert value.session.refresh_token == "synthetic-ios-refresh"
    assert await file_bytes(value.device_path) == value.initial_device
    assert await file_bytes(value.session.session_file) == value.initial_session
    assert value.adapter._stage is None


async def accepted_auth(value):
    value.session.hash_token, value.session.refresh_token = (
        "synthetic-android-access",
        "synthetic-android-refresh",
    )
    await value.session.async_persist_session_to_disk()
    await value.adapter.async_finish_auth(True)


async def test_prepare_stages_android_in_memory_without_changing_durable_bytes(binding):
    await binding.adapter.async_prepare()
    assert binding.device.profile_context.current.callby == "OWA_10"
    assert (
        binding.device.get_device_identifiers()["idDevice"] == "synthetic-fcm-address"
    )
    assert (
        binding.device.get_device_identifiers()["uuid"]
        == binding.initial_identifiers["uuid"]
    )
    assert binding.session.hash_token is None and binding.session.refresh_token is None
    assert await file_bytes(binding.device_path) == binding.initial_device
    assert await file_bytes(binding.session.session_file) == binding.initial_session
    assert binding.adapter.diagnostics()["binding_state"] == "pending"
    binding.receiver.async_start.assert_awaited_once()


async def test_accepted_auth_commits_device_and_session_for_restart(binding, tmp_path):
    await binding.adapter.async_prepare()
    await accepted_auth(binding)
    assert binding.adapter.diagnostics()["binding_state"] == "bound"
    assert binding.adapter._stage is None
    persisted = json.loads(await file_bytes(binding.device_path))
    assert persisted["idDevice"] == "synthetic-fcm-address"
    assert persisted["protocol_profile"] == "android"
    assert persisted["uuid"] == binding.initial_identifiers["uuid"]
    restored = build_my_verisure_composition_root(project_root=tmp_path)
    await restored.get(DeviceManager).async_ensure_device_identifiers()
    assert restored.get(DeviceManager).profile_context.current.callby == "OWA_10"
    assert (
        json.loads(await file_bytes(restored.get(SessionManager).session_file))[
            "hash_token"
        ]
        == "synthetic-android-access"
    )


async def test_rejected_auth_restores_device_session_bytes_and_keeps_cooldown(binding):
    await binding.adapter.async_prepare()
    binding.session.hash_token, binding.session.refresh_token = (
        "synthetic-rejected-access",
        "synthetic-rejected-refresh",
    )
    await binding.session.async_persist_session_to_disk()
    binding.session.record_service_blocked(600)
    await binding.adapter.async_finish_auth(False)
    await assert_restored(binding)
    assert binding.session.is_service_blocked()
    assert binding.adapter.diagnostics()["binding_state"] == "reauth_required"
    await binding.adapter.async_prepare()
    binding.receiver.async_prepare.assert_awaited_once()


async def test_prepare_cancellation_drains_rollback_even_when_cancelled_twice(
    binding, monkeypatch
):
    started, restoring, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    original_restore = binding.device._binding_store.restore_bytes

    async def start():
        started.set()
        await asyncio.Event().wait()

    async def delayed_restore(*args, **kwargs):
        restoring.set()
        await release.wait()
        return await original_restore(*args, **kwargs)

    binding.receiver.async_start.side_effect = start
    monkeypatch.setattr(binding.device._binding_store, "restore_bytes", delayed_restore)
    job = asyncio.create_task(binding.adapter.async_prepare())
    try:
        await started.wait()
        binding.session.record_service_blocked(600)
        job.cancel()
        await restoring.wait()
        job.cancel()
        await asyncio.sleep(0)
        assert not job.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await job
        await assert_restored(binding)
        assert binding.session.is_service_blocked()
        assert not any(
            task.get_name() == "my_verisure_push_binding" and not task.done()
            for task in asyncio.all_tasks()
        )
    finally:
        release.set()
        await asyncio.gather(job, return_exceptions=True)


async def test_failed_device_commit_rolls_back_all_auth_bytes(binding, monkeypatch):
    await binding.adapter.async_prepare()
    binding.session.hash_token = "synthetic-new-access"
    await binding.session.async_persist_session_to_disk()
    monkeypatch.setattr(
        binding.device._binding_store,
        "save",
        AsyncMock(side_effect=OSError("synthetic write failure")),
    )
    with pytest.raises(OSError, match="synthetic write failure"):
        await binding.adapter.async_finish_auth(True)
    await assert_restored(binding)
    assert binding.adapter.diagnostics()["binding_state"] == "degraded"


async def test_token_rotation_callback_only_marks_pending_until_next_auth(binding):
    await binding.adapter.async_prepare()
    await accepted_auth(binding)
    before_device, before_session = (
        await file_bytes(binding.device_path),
        await file_bytes(binding.session.session_file),
    )
    binding.options["on_token_changed"]("synthetic-rotated-address")
    assert binding.adapter.diagnostics()["binding_state"] == "pending"
    assert binding.session.hash_token == "synthetic-android-access"
    assert binding.session.refresh_token == "synthetic-android-refresh"
    assert (
        binding.device.get_device_identifiers()["idDevice"] == "synthetic-fcm-address"
    )
    assert await file_bytes(binding.device_path) == before_device
    assert await file_bytes(binding.session.session_file) == before_session
    binding.receiver.async_prepare.assert_awaited_once()
    binding.receiver.async_prepare.return_value = "synthetic-rotated-address"
    await binding.adapter.async_prepare()
    assert binding.session.hash_token is None
    assert binding.session.refresh_token == "synthetic-android-refresh"
    assert await file_bytes(binding.device_path) == before_device


async def test_unchanged_cached_push_address_keeps_existing_auth_and_bytes(binding):
    await binding.device.async_set_push_token("synthetic-fcm-address")
    binding.session.hash_token, binding.session.refresh_token = (
        "synthetic-cached-access",
        "synthetic-cached-refresh",
    )
    await binding.session.async_persist_session_to_disk()
    before_device, before_session = (
        await file_bytes(binding.device_path),
        await file_bytes(binding.session.session_file),
    )
    await binding.adapter.async_prepare()
    assert binding.session.hash_token == "synthetic-cached-access"
    assert binding.session.refresh_token == "synthetic-cached-refresh"
    await binding.adapter.async_finish_auth(True)
    assert await file_bytes(binding.device_path) == before_device
    assert await file_bytes(binding.session.session_file) == before_session


async def test_unload_drains_staged_rollback_before_stopping_transport(
    binding, monkeypatch
):
    await binding.adapter.async_prepare()
    entered, release = asyncio.Event(), asyncio.Event()
    original_restore = binding.device._binding_store.restore_bytes

    async def delayed_restore(*args, **kwargs):
        entered.set()
        await release.wait()
        return await original_restore(*args, **kwargs)

    monkeypatch.setattr(binding.device._binding_store, "restore_bytes", delayed_restore)
    job = asyncio.create_task(binding.adapter.async_stop())
    try:
        await entered.wait()
        binding.receiver.async_stop.assert_not_awaited()
        assert not job.done()
        release.set()
        await job
        await assert_restored(binding)
        binding.receiver.async_stop.assert_awaited_once()
        assert binding.adapter.hub._closed
    finally:
        release.set()
        await asyncio.gather(job, return_exceptions=True)


async def test_concurrent_accepted_and_rejected_finish_cannot_split_device_and_session(
    binding, monkeypatch
):
    await binding.adapter.async_prepare()
    binding.session.hash_token, binding.session.refresh_token = (
        "synthetic-android-access",
        "synthetic-android-refresh",
    )
    await binding.session.async_persist_session_to_disk()
    entered, release = asyncio.Event(), asyncio.Event()
    original_save = binding.device._binding_store.save

    async def delayed_save(*args, **kwargs):
        entered.set()
        await release.wait()
        return await original_save(*args, **kwargs)

    monkeypatch.setattr(binding.device._binding_store, "save", delayed_save)
    accepted = asyncio.create_task(binding.adapter.async_finish_auth(True))
    rejected = None
    try:
        await entered.wait()
        rejected = asyncio.create_task(binding.adapter.async_finish_auth(False))
        await asyncio.sleep(0)
        release.set()
        await asyncio.gather(accepted, rejected)
        assert (
            binding.device.get_device_identifiers()["idDevice"]
            == "synthetic-fcm-address"
        )
        assert binding.session.hash_token == "synthetic-android-access"
        assert (
            json.loads(await file_bytes(binding.session.session_file))["hash_token"]
            == "synthetic-android-access"
        )
        assert binding.adapter._stage is None
    finally:
        release.set()
        await asyncio.gather(
            accepted,
            *([rejected] if rejected is not None else []),
            return_exceptions=True,
        )


async def test_cancelled_unload_finishes_rollback_and_transport_close(
    binding, monkeypatch
):
    await binding.adapter.async_prepare()
    entered, release = asyncio.Event(), asyncio.Event()
    original_restore = binding.device._binding_store.restore_bytes

    async def delayed_restore(*args, **kwargs):
        entered.set()
        await release.wait()
        return await original_restore(*args, **kwargs)

    monkeypatch.setattr(binding.device._binding_store, "restore_bytes", delayed_restore)
    job = asyncio.create_task(binding.adapter.async_stop())
    try:
        await entered.wait()
        job.cancel()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await job
        await assert_restored(binding)
        binding.receiver.async_stop.assert_awaited_once()
        assert binding.adapter.hub._closed
    finally:
        release.set()
        await asyncio.gather(job, return_exceptions=True)


async def test_rotation_during_pending_auth_cannot_report_obsolete_address_bound(
    binding,
):
    await binding.adapter.async_prepare()
    binding.options["on_token_changed"]("synthetic-rotated-address")
    await accepted_auth(binding)
    assert binding.adapter.diagnostics()["binding_state"] == "pending"
    assert binding.session.hash_token == "synthetic-android-access"
    binding.receiver.async_prepare.assert_awaited_once()

"""Drain entry operations before rolling back notification binding on unload.

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
from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.application.coordinator_authentication import (
    CoordinatorAuthenticationDecision,
)
from custom_components.my_verisure.core.application.coordinator_failure import (
    CoordinatorFailureClassifier,
)
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.models.alarm import ArmResult
from custom_components.my_verisure.core.dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager

pytestmark = [pytest.mark.homeassistant, pytest.mark.asyncio]


@pytest.fixture
async def local_entry(hass, tmp_path, monkeypatch):
    """Use actual private stores and binding, with no provider transport."""
    root = build_my_verisure_composition_root(project_root=tmp_path, push_enabled=True)
    device, session = root.get(DeviceManager), root.get(SessionManager)
    await device.async_ensure_device_identifiers()
    session.hash_token, session.refresh_token = (
        "synthetic-old-access",
        "synthetic-old-refresh",
    )
    await session.async_persist_session_to_disk()
    files = root.get(FileManager)
    device_path = files.get_file_path("device_identifiers.json")
    before_device = await asyncio.to_thread(device_path.read_bytes)
    before_session = await asyncio.to_thread(Path(session.session_file).read_bytes)
    receiver = SimpleNamespace(
        async_prepare=AsyncMock(return_value="synthetic-fcm-address"),
        async_start=AsyncMock(),
        async_stop=AsyncMock(),
        diagnostics=Mock(return_value={}),
        request_state_save=Mock(),
    )
    monkeypatch.setattr(push, "PushReceiver", lambda *args, **kwargs: receiver)
    adapter = push.HomeAssistantPush(
        hass, root, installation_id="synthetic-home", entry_id="synthetic-entry"
    )
    value = object.__new__(MyVerisureDataUpdateCoordinator)
    value.hass = hass
    value.installation_id, value._dev_mode = "synthetic-home", False
    value.config_entry = SimpleNamespace(options={}, data={})
    value._login_lock = asyncio.Lock()
    value._push = adapter
    value._notification_runtime = SimpleNamespace(
        async_close=AsyncMock(), state_synchronized=Mock(), command_completed=Mock()
    )
    value.async_shutdown = AsyncMock()
    value.session_manager = session
    value.composition_root = root
    value._camera_refresh_lock = asyncio.Lock()
    value._failure_classifier = CoordinatorFailureClassifier()
    value.notifications = SimpleNamespace(notify=AsyncMock())
    value.data = {
        "detailed_installation": {
            "installation": {
                "panel": "synthetic-panel",
                "capabilities": "synthetic-caps",
            }
        }
    }
    value._async_ensure_installation_context = AsyncMock(
        return_value=("synthetic-panel", "synthetic-caps")
    )

    async def publish(snapshot, *args, **kwargs):
        value.data = snapshot

    value.refresh_effects = SimpleNamespace(apply=AsyncMock(side_effect=publish))
    result = SimpleNamespace(
        coordinator=value,
        adapter=adapter,
        device=device,
        session=session,
        receiver=receiver,
        device_path=device_path,
        before_device=before_device,
        before_session=before_session,
    )
    yield result
    await adapter.async_stop()


@pytest.mark.parametrize("cancel_cleanup", [False, True])
async def test_unload_owns_authentication_until_its_cancelled_finally_finishes(
    local_entry, cancel_cleanup
):
    """An in-flight login must not commit candidate credentials after rollback."""
    value = local_entry
    entered, cancelled, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def authenticate():
        await value.adapter.async_prepare()
        entered.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.set()
            await release.wait()
            # Represents an already-started persistence completion during auth cleanup.
            value.session.hash_token = "synthetic-candidate-access"
            await value.session.async_persist_session_to_disk()
            raise

    value.coordinator._async_login_transaction = authenticate
    login = asyncio.create_task(value.coordinator.async_login())
    cleanup = None
    cancellation_waiter = None
    try:
        await asyncio.wait_for(entered.wait(), 2)
        cleanup = asyncio.create_task(value.coordinator.async_cleanup())
        cancellation_waiter = asyncio.create_task(cancelled.wait())
        finished, _ = await asyncio.wait(
            (cleanup, cancellation_waiter),
            return_when=asyncio.FIRST_COMPLETED,
            timeout=2,
        )
        assert cancellation_waiter in finished, (
            "Unload returned without cancelling the active login"
        )
        assert not cleanup.done(), (
            "Unload abandoned an authentication cleanup still writing candidate state"
        )
        value.receiver.async_stop.assert_not_awaited()
        if cancel_cleanup:
            cleanup.cancel()
            cleanup.cancel()
        release.set()
        if cancel_cleanup:
            with pytest.raises(asyncio.CancelledError):
                await cleanup
        else:
            await cleanup
        assert login.done()
        assert isinstance(
            (await asyncio.gather(login, return_exceptions=True))[0],
            asyncio.CancelledError,
        )
        assert value.session.hash_token == "synthetic-old-access"
        assert (
            await asyncio.to_thread(value.device_path.read_bytes) == value.before_device
        )
        assert (
            await asyncio.to_thread(Path(value.session.session_file).read_bytes)
            == value.before_session
        )
        assert (
            json.loads(await asyncio.to_thread(value.device_path.read_bytes)).get(
                "protocol_profile"
            )
            != "android"
        )
        value.receiver.async_stop.assert_awaited_once()
    finally:
        release.set()
        if not login.done():
            login.cancel()
        if cancellation_waiter is not None:
            cancellation_waiter.cancel()
        await asyncio.gather(
            login,
            *([cleanup] if cleanup is not None else []),
            *([cancellation_waiter] if cancellation_waiter is not None else []),
            return_exceptions=True,
        )


@pytest.mark.parametrize(
    "operation",
    ["login", "command", "native_read", "targeted_read", "full_read", "camera"],
)
async def test_closed_coordinator_never_reenters_provider_ports(local_entry, operation):
    """Late service or timer callbacks cannot restart I/O after entry cleanup."""
    value = local_entry.coordinator
    await value.async_cleanup()
    authentication = AsyncMock(return_value=True)
    value._async_login_transaction = authentication
    command = AsyncMock(return_value=ArmResult(True, "synthetic", confirmed_state="E"))
    targeted = AsyncMock(return_value=SimpleNamespace(dict=lambda: {"success": False}))
    native = AsyncMock(return_value={"external": {"status": True}})
    full = AsyncMock(return_value=value.data)
    camera = AsyncMock(return_value=SimpleNamespace(failed_refreshes=0))
    value.alarm_use_case = SimpleNamespace(arm_home=command, get_alarm_status=targeted)
    value.snapshot_service = SimpleNamespace(refresh=full)
    value.authentication_policy = SimpleNamespace(
        authenticate=AsyncMock(
            return_value=CoordinatorAuthenticationDecision(authenticated=True)
        )
    )
    value.coordinator_camera_refresh = SimpleNamespace(run=camera)
    value.composition_root = SimpleNamespace(
        get=Mock(return_value=SimpleNamespace(get_current_alarm_status=native))
    )
    calls = {
        "login": value.async_login,
        "command": value.async_arm_home,
        "native_read": value.async_refresh_current_alarm_state,
        "targeted_read": value._async_refresh_alarm_only,
        "full_read": value._async_update_data,
        "camera": value.async_refresh_camera_images,
    }
    try:
        await calls[operation]()
    except (MyVerisureError, asyncio.CancelledError):
        pass
    assert authentication.await_count == 0
    assert command.await_count == 0
    assert targeted.await_count == 0
    assert native.await_count == 0
    assert full.await_count == 0
    assert camera.await_count == 0

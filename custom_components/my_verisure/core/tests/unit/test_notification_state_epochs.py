"""Prevent notification reconciliation from overwriting newer alarm operations.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.application.coordinator_authentication import (
    CoordinatorAuthenticationDecision,
)
from custom_components.my_verisure.core.application.coordinator_failure import (
    CoordinatorFailureClassifier,
)
from custom_components.my_verisure.core.application.models.alarm import (
    ArmResult,
    DisarmResult,
)


def coordinator(installation="synthetic-home"):
    value = object.__new__(MyVerisureDataUpdateCoordinator)
    value.installation_id = installation
    value._dev_mode = False
    value.config_entry = SimpleNamespace(options={}, data={})
    value.session_manager = Mock()
    value.session_manager.get_current_hash_token.return_value = "synthetic-session"
    value._installation_auth_hash = "synthetic-session"
    value.async_login = AsyncMock(return_value=True)
    value._async_ensure_installation_context = AsyncMock(
        return_value=("synthetic-panel", "synthetic-caps")
    )
    value.authentication_policy = SimpleNamespace(
        authenticate=AsyncMock(
            return_value=CoordinatorAuthenticationDecision(authenticated=True)
        )
    )
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
    value.alarm_use_case = SimpleNamespace(
        arm_home=AsyncMock(
            return_value=ArmResult(True, "synthetic", confirmed_state="E")
        ),
        arm_night=AsyncMock(
            return_value=ArmResult(True, "synthetic", confirmed_state="C")
        ),
        disarm=AsyncMock(
            return_value=DisarmResult(True, "synthetic", confirmed_state="D")
        ),
    )

    async def publish(snapshot, *args, **kwargs):
        value.data = snapshot

    value.refresh_effects = SimpleNamespace(apply=AsyncMock(side_effect=publish))
    return value


@pytest.mark.parametrize("kind", ["targeted", "full"])
async def test_read_started_before_confirmed_command_cannot_publish_old_state(kind):
    value = coordinator()
    entered, release = asyncio.Event(), asyncio.Event()
    older = {"success": True, "status": "ALARM", "data": {"external": {"status": True}}}

    async def delayed(*args, **kwargs):
        entered.set()
        await release.wait()
        if kind == "targeted":
            return SimpleNamespace(dict=lambda: older)
        return {**value.data, "alarm_status": older}

    if kind == "targeted":
        value.alarm_use_case.get_alarm_status = AsyncMock(side_effect=delayed)
        pending = asyncio.create_task(value._async_refresh_alarm_only())
    else:
        value.snapshot_service = SimpleNamespace(refresh=AsyncMock(side_effect=delayed))
        pending = asyncio.create_task(value._async_update_data())
    await entered.wait()
    await value.async_disarm()
    release.set()
    result = await pending
    assert value.data["alarm_status"]["status"] == "OK"
    assert result["alarm_status"]["status"] == "OK"
    assert value.refresh_effects.apply.await_count == 1


async def test_entries_share_one_lock_for_complete_compound_commands():
    first, second = coordinator(), coordinator()
    entered, release = asyncio.Event(), asyncio.Event()
    order = []

    async def compound(*args, **kwargs):
        order.append("interior")
        entered.set()
        await release.wait()
        order.append("perimeter")
        return ArmResult(True, "synthetic", confirmed_state="C")

    async def disarm(*args, **kwargs):
        order.append("disarm")
        return DisarmResult(True, "synthetic", confirmed_state="D")

    first.alarm_use_case.arm_night = AsyncMock(side_effect=compound)
    second.alarm_use_case.disarm = AsyncMock(side_effect=disarm)
    pending = asyncio.create_task(first.async_arm_night())
    await entered.wait()
    next_command = asyncio.create_task(second.async_disarm())
    try:
        await asyncio.sleep(0)
        assert order == ["interior"]
    finally:
        release.set()
        await asyncio.gather(pending, next_command)
    assert order == ["interior", "perimeter", "disarm"]


async def test_cancelled_started_command_invalidates_known_state_and_releases_lock():
    value = coordinator()
    await value._async_apply_command_state(
        ArmResult(True, "synthetic", confirmed_state="E")
    )
    entered = asyncio.Event()

    async def pending_operation(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    value.alarm_use_case.arm_home = AsyncMock(side_effect=pending_operation)
    pending = asyncio.create_task(value.async_arm_home())
    await entered.wait()
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pending
    assert value.data["alarm_status"]["status"] is None
    assert (await value.async_disarm()).confirmed_state == "D"


async def test_native_refresh_does_not_use_legacy_full_or_radio_reader():
    value = coordinator()
    zones = {
        "internal": {key: {"status": False} for key in ("day", "night", "total")},
        "external": {"status": True},
    }
    native = SimpleNamespace(get_current_alarm_status=AsyncMock(return_value=zones))
    value.composition_root = SimpleNamespace(get=Mock(return_value=native))
    value.alarm_use_case.get_alarm_status = AsyncMock(
        side_effect=AssertionError("radio reader must not run")
    )
    value._async_update_data = AsyncMock(
        side_effect=AssertionError("full snapshot must not run")
    )
    result = await value.async_refresh_current_alarm_state()
    assert result["alarm_status"]["data"] == zones
    native.get_current_alarm_status.assert_awaited_once_with(
        "synthetic-home", "synthetic-panel", "synthetic-caps"
    )
    value.alarm_use_case.get_alarm_status.assert_not_awaited()
    value._async_update_data.assert_not_awaited()


async def test_native_refresh_obsolete_after_other_entry_command_returns_none():
    value, other = coordinator(), coordinator()
    entered, release = asyncio.Event(), asyncio.Event()

    async def read(*args):
        entered.set()
        await release.wait()
        return {"external": {"status": True}}

    value.composition_root = SimpleNamespace(
        get=Mock(return_value=SimpleNamespace(get_current_alarm_status=read))
    )
    pending = asyncio.create_task(value.async_refresh_current_alarm_state())
    await entered.wait()
    await other.async_disarm()
    release.set()
    assert await pending is None
    value.refresh_effects.apply.assert_not_awaited()


async def test_native_refresh_during_command_does_not_query_provider():
    value = coordinator()
    entered, release = asyncio.Event(), asyncio.Event()

    async def operation(*args, **kwargs):
        entered.set()
        await release.wait()
        return ArmResult(True, "synthetic", confirmed_state="E")

    value.alarm_use_case.arm_home = AsyncMock(side_effect=operation)
    native = SimpleNamespace(get_current_alarm_status=AsyncMock())
    value.composition_root = SimpleNamespace(get=Mock(return_value=native))
    pending = asyncio.create_task(value.async_arm_home())
    await entered.wait()
    try:
        assert await value.async_refresh_current_alarm_state() is None
        native.get_current_alarm_status.assert_not_awaited()
    finally:
        release.set()
        await pending


@pytest.mark.parametrize("cancel_times", [1, 2])
async def test_cancelled_snapshot_write_is_drained_before_new_command_publication(
    cancel_times,
):
    value = coordinator()
    entered, release = asyncio.Event(), asyncio.Event()
    writers = []
    publications = []
    persisted = []
    older = {"success": True, "status": "ALARM", "data": {"external": {"status": True}}}
    value.alarm_use_case.get_alarm_status = AsyncMock(
        return_value=SimpleNamespace(dict=lambda: older)
    )

    async def writer(snapshot):
        if not persisted and snapshot["alarm_status"]["status"] == "ALARM":
            entered.set()
            await release.wait()
        persisted.append(snapshot["alarm_status"]["status"])

    async def publish_and_write(snapshot, *args, **kwargs):
        publications.append(asyncio.current_task())
        value.data = snapshot
        # Emulate to_thread: cancelling the waiter does not stop its write.
        task = asyncio.create_task(writer(snapshot))
        writers.append(task)
        await asyncio.shield(task)

    value.refresh_effects.apply = AsyncMock(side_effect=publish_and_write)
    pending_read = asyncio.create_task(value._async_refresh_alarm_only())
    await entered.wait()
    pending_read.cancel()
    next_command = asyncio.create_task(value.async_disarm())
    try:
        await asyncio.sleep(0)
        if cancel_times == 2:
            pending_read.cancel()
        await asyncio.sleep(0)
        value.alarm_use_case.disarm.assert_not_awaited()
    finally:
        release.set()
        await asyncio.gather(pending_read, next_command, return_exceptions=True)
        await asyncio.gather(*writers)
    assert pending_read.cancelled()
    assert persisted == ["ALARM", "OK"]
    assert value.data["alarm_status"]["status"] == "OK"
    assert all(task.done() for task in publications + writers)


async def test_cleanup_waits_for_owned_snapshot_publication():
    value = coordinator()
    value.async_shutdown = AsyncMock()
    entered, release = asyncio.Event(), asyncio.Event()
    publication_tasks = []
    value.alarm_use_case.get_alarm_status = AsyncMock(
        return_value=SimpleNamespace(dict=lambda: {"status": "ALARM"})
    )

    async def publish(snapshot, *args, **kwargs):
        publication_tasks.append(asyncio.current_task())
        entered.set()
        await release.wait()
        value.data = snapshot

    value.refresh_effects.apply = AsyncMock(side_effect=publish)
    pending = asyncio.create_task(value._async_refresh_alarm_only())
    await entered.wait()
    cleanup = asyncio.create_task(value.async_cleanup())
    try:
        await asyncio.sleep(0)
        assert not cleanup.done()
    finally:
        release.set()
        results = await asyncio.gather(pending, cleanup, return_exceptions=True)
    assert isinstance(results[0], asyncio.CancelledError)
    assert results[1] is None
    assert publication_tasks and all(task.done() for task in publication_tasks)

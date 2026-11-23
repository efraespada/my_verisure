"""Exercise real notification composition with HA registries and local read ports.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure import notification_runtime
from custom_components.my_verisure.camera import camera_unique_id
from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.api.notification_mapper import (
    NotificationMapper,
)
from custom_components.my_verisure.core.api.provider_request_gate import (
    get_provider_request_gate,
)
from custom_components.my_verisure.core.application.models.device import Device
from custom_components.my_verisure.core.application.notification_refresh import (
    BackgroundReadBudget,
)
from custom_components.my_verisure.core.application.notifications import (
    NotificationEvent,
    NotificationHub,
    NotificationNotice,
)
from custom_components.my_verisure.core.const import (
    CONF_EXTERNAL_PHOTO_UPDATES,
    CONF_PUSH_STATE_REFRESH,
    DOMAIN,
)
from ..core.use_cases.implementations.refresh_camera_images_use_case_impl import (
    RefreshCameraImagesUseCaseImpl,
)

pytestmark = [pytest.mark.homeassistant, pytest.mark.asyncio]


class FakeRoot:
    """Resolve only local doubles; no provider session can be constructed."""

    def __init__(self, camera):
        self.camera = camera
        self.device = SimpleNamespace(profile_context=object())

    def get(self, port):
        return {CameraClient: self.camera, DeviceManager: self.device}[port]


def make_notice(kind="photo_reported", **changes):
    event = NotificationEvent(
        kind,
        "reported",
        "synthetic-event",
        "synthetic-correlation",
        "photo",
        "installation",
        1000.0,
        provider_request="INF" if kind == "photo_reported" else "SMARTNOT",
        occurred_at=1000.0,
        freshness="fresh",
    )
    value = NotificationNotice(event, signal_id="123", photo_type=0)
    return replace(value, **changes)


@pytest.fixture
def runtime_factory(hass):
    created = []

    def build(*, enabled=True, entry_id=None):
        entry_id = entry_id or f"synthetic-entry-{len(created)}"
        entry = MockConfigEntry(
            domain=DOMAIN,
            entry_id=entry_id,
            options={
                CONF_PUSH_STATE_REFRESH: True,
                CONF_EXTERNAL_PHOTO_UPDATES: True,
            },
        )
        entry.add_to_hass(hass)
        device = {"type": "YR", "code": "7", "is_active": True}
        registry_entry = er.async_get(hass).async_get_or_create(
            "camera",
            DOMAIN,
            camera_unique_id(entry.entry_id, device),
            suggested_object_id=f"synthetic_camera_{len(created)}",
            config_entry=entry,
        )
        camera = SimpleNamespace(
            get_existing_photo=AsyncMock(
                return_value={
                    "success": True,
                    "camera_identifier": "YR07",
                    "images_saved": 3,
                }
            ),
            request_image=AsyncMock(
                return_value=SimpleNamespace(successful_requests=1, signal_id="123")
            ),
            get_images=AsyncMock(
                return_value={"success": True, "images_saved": 3, "signal_id": "123"}
            ),
        )
        installation = SimpleNamespace(
            get_installation_services=AsyncMock(
                return_value=SimpleNamespace(
                    installation=SimpleNamespace(
                        panel="synthetic-panel",
                        capabilities="synthetic-caps",
                        devices=[
                            Device(
                                "synthetic-device",
                                "7",
                                "synthetic",
                                "YR",
                                "",
                                True,
                                "CAM",
                                True,
                            ),
                        ],
                    )
                )
            )
        )
        use_case = RefreshCameraImagesUseCaseImpl(camera, installation)
        coordinator = SimpleNamespace(
            hass=hass,
            config_entry=entry,
            installation_id="synthetic-house",
            _push_enabled=enabled,
            data={
                "detailed_installation": {
                    "installation": {
                        "devices": [device],
                        "services": [
                            {"id_service": "520", "active": True, "visible": True},
                        ],
                    }
                },
                "alarm_status": {
                    "success": True,
                    "data": {
                        "internal": {
                            "day": {"status": False},
                            "night": {"status": False},
                            "total": {"status": False},
                        },
                        "external": {"status": False},
                    },
                },
            },
            composition_root=FakeRoot(camera),
            session_manager=object(),
            async_login=AsyncMock(return_value=True),
            _async_ensure_installation_context=AsyncMock(
                return_value=("synthetic-panel", "synthetic-caps")
            ),
            async_refresh_current_alarm_state=AsyncMock(),
            async_update_listeners=Mock(),
            _camera_refresh_lock=asyncio.Lock(),
            refresh_camera_images_use_case=use_case,
        )
        operation = get_provider_request_gate().get_operation_state(entry_id)
        coordinator._get_operation_state = lambda: operation
        hub = NotificationHub(
            entry_id, NotificationMapper(coordinator.installation_id, entry_id)
        )
        events = []
        hub.subscribe(events.append)
        hub.activate()
        runtime = notification_runtime.NotificationRuntime(coordinator, hub)
        value = SimpleNamespace(
            runtime=runtime,
            coordinator=coordinator,
            camera=camera,
            hub=hub,
            events=events,
            operation=operation,
            subject=registry_entry.entity_id,
        )
        created.append(value)
        return value

    return build


@pytest.mark.parametrize("enabled", [True, False])
async def test_local_photo_ready_waits_for_persistence_even_without_push(
    runtime_factory, enabled
):
    value = runtime_factory(enabled=enabled)
    value.runtime.activate()
    entered, release = asyncio.Event(), asyncio.Event()
    persisted = False

    async def persist(*args, **kwargs):
        nonlocal persisted
        entered.set()
        await release.wait()
        persisted = True
        return {"success": True, "images_saved": 3, "signal_id": "123"}

    value.camera.get_images.side_effect = persist
    job = asyncio.create_task(
        value.coordinator.refresh_camera_images_use_case.refresh_camera_images(
            "synthetic-house"
        )
    )
    try:
        await entered.wait()
        assert not value.events
        release.set()
        result = await job
        assert persisted and result.successful_refreshes == 1
        assert len(value.events) == 1
        event = value.events[0]
        assert (event.kind, event.subject_entity_id, event.verification) == (
            "photo_ready",
            value.subject,
            "image_commit",
        )
        assert dict(event.facts) == {"image_count": 3, "origin": "local_request"}
        assert (
            "signal_id" not in event.public_data()
            and "idSignal" not in event.public_data()
        )
        assert "123" not in event.public_data().values()
    finally:
        release.set()
        await asyncio.gather(job, return_exceptions=True)
        await value.runtime.async_close()


async def test_external_photo_busy_lock_defers_without_auth_then_reads_exact_context(
    runtime_factory,
):
    value = runtime_factory()
    await value.coordinator._camera_refresh_lock.acquire()
    try:
        assert await value.runtime._verify(make_notice()) is False
        value.coordinator.async_login.assert_not_awaited()
        value.camera.get_existing_photo.assert_not_awaited()
    finally:
        value.coordinator._camera_refresh_lock.release()
    assert await value.runtime._verify(make_notice()) is True
    value.camera.get_existing_photo.assert_awaited_once_with(
        "synthetic-house",
        "synthetic-panel",
        "synthetic-caps",
        signal_id="123",
        expected_camera_codes=["YR07"],
        event_timestamp=1000.0,
    )
    value.camera.request_image.assert_not_awaited()
    value.camera.get_images.assert_not_awaited()
    assert len(value.events) == 1 and value.events[0].subject_entity_id == value.subject
    value.coordinator.async_update_listeners.assert_called_once()


@pytest.mark.parametrize("camera_identifier,active", [("YR08", True), ("YR07", False)])
async def test_unowned_or_inactive_photo_never_emits(
    runtime_factory, camera_identifier, active
):
    value = runtime_factory()
    value.coordinator.data["detailed_installation"]["installation"]["devices"][0][
        "is_active"
    ] = active
    value.camera.get_existing_photo.return_value["camera_identifier"] = (
        camera_identifier
    )
    assert await value.runtime._verify(make_notice()) is True
    assert not value.events
    value.coordinator.async_update_listeners.assert_not_called()
    assert value.camera.get_existing_photo.await_args.kwargs[
        "expected_camera_codes"
    ] == (["YR07"] if active else [])


async def test_incident_requires_effective_service_and_uses_renewed_context(
    runtime_factory, monkeypatch
):
    value = runtime_factory()
    read = AsyncMock(return_value=("123",))
    factory = Mock(return_value=SimpleNamespace(get_open_incidents=read))
    monkeypatch.setattr(notification_runtime, "NotificationClient", factory)
    value.coordinator._async_ensure_installation_context.return_value = (
        "renewed-panel",
        "renewed-caps",
    )
    assert (
        await value.runtime._verify(make_notice("security_incident_reported")) is True
    )
    factory.assert_called_once_with(
        value.coordinator.session_manager,
        value.coordinator.composition_root.device.profile_context,
    )
    read.assert_awaited_once_with("synthetic-house", "renewed-panel", "renewed-caps")
    assert dict(value.events[0].facts) == {"incident_state": "open"}
    assert "signal_id" not in value.events[0].public_data()
    assert "123" not in value.events[0].public_data().values()


@pytest.mark.parametrize("phase", ["before", "after_context"])
async def test_missing_incident_permission_is_consumed_without_query(
    runtime_factory, monkeypatch, phase
):
    value = runtime_factory()
    factory = Mock(side_effect=AssertionError("No incident query without entitlement"))
    monkeypatch.setattr(notification_runtime, "NotificationClient", factory)

    async def remove_permission():
        value.coordinator.data["detailed_installation"]["installation"]["services"] = []
        return "new-panel", "new-caps"

    if phase == "before":
        await remove_permission()
    else:
        value.coordinator._async_ensure_installation_context.side_effect = (
            remove_permission
        )
    assert (
        await value.runtime._verify(make_notice("security_incident_reported")) is True
    )
    factory.assert_not_called()
    assert not value.events


@pytest.mark.parametrize("transition", ["epoch", "busy"])
async def test_incident_snapshot_invalidated_during_read_is_pending(
    runtime_factory, monkeypatch, transition
):
    value = runtime_factory()

    async def read(*args):
        if transition == "epoch":
            value.operation.generation += 1
        else:
            await value.operation.lock.acquire()
        return ("123",)

    monkeypatch.setattr(
        notification_runtime,
        "NotificationClient",
        Mock(return_value=SimpleNamespace(get_open_incidents=read)),
    )
    try:
        assert (
            await value.runtime._verify(make_notice("security_incident_reported"))
            is False
        )
        assert not value.events
    finally:
        if value.operation.lock.locked():
            value.operation.lock.release()


@pytest.mark.parametrize("transition", ["generation", "busy"])
async def test_incident_operation_invalidated_during_context_never_queries(
    runtime_factory, monkeypatch, transition
):
    """Context renewal may await; recheck operation admission before wire I/O."""
    value = runtime_factory()
    factory = Mock(
        side_effect=AssertionError(
            "A superseded context must not reach the incident reader"
        )
    )
    monkeypatch.setattr(notification_runtime, "NotificationClient", factory)

    async def context():
        if transition == "generation":
            value.operation.generation += 1
        else:
            await value.operation.lock.acquire()
        return "renewed-panel", "renewed-caps"

    value.coordinator._async_ensure_installation_context.side_effect = context
    try:
        assert (
            await value.runtime._verify(make_notice("security_incident_reported"))
            is False
        )
        factory.assert_not_called()
        assert not value.events
    finally:
        if value.operation.lock.locked():
            value.operation.lock.release()


async def test_incident_response_from_replaced_session_stays_pending(
    runtime_factory, monkeypatch
):
    """A fresh lookup of credentials must not legitimize an older response."""
    value = runtime_factory()
    value.coordinator.session_manager = SimpleNamespace(
        hash_token="synthetic-old-session"
    )

    async def read(*args):
        value.coordinator.session_manager.hash_token = "synthetic-replaced-session"
        return ("123",)

    monkeypatch.setattr(
        notification_runtime,
        "NotificationClient",
        Mock(return_value=SimpleNamespace(get_open_incidents=read)),
    )
    assert (
        await value.runtime._verify(make_notice("security_incident_reported")) is False
    )
    assert not value.events


async def test_external_photo_cannot_publish_after_installation_epoch_changes(
    runtime_factory,
):
    value = runtime_factory()

    async def read(*args, **kwargs):
        value.operation.generation += 1
        return {"success": True, "camera_identifier": "YR07", "images_saved": 3}

    value.camera.get_existing_photo.side_effect = read
    assert await value.runtime._verify(make_notice()) is False
    assert not value.events


async def test_entries_share_budget_but_keep_state_ports_and_publication_scoped(
    runtime_factory,
):
    first, second = runtime_factory(), runtime_factory()
    first.runtime.activate()
    second.runtime.activate()
    try:
        assert first.runtime._scheduler._budget is second.runtime._scheduler._budget
        assert isinstance(first.runtime._scheduler._budget, BackgroundReadBudget)
        assert await first.runtime._verify(make_notice()) is True
        first.camera.get_existing_photo.assert_awaited_once()
        second.camera.get_existing_photo.assert_not_awaited()
        assert len(first.events) == 1 and not second.events
        assert first.events[0].subject_entity_id == first.subject
        assert first.subject != second.subject
    finally:
        await first.runtime.async_close()
        await second.runtime.async_close()


async def test_runtime_close_cancels_and_drains_inflight_read(runtime_factory):
    value = runtime_factory()
    value.runtime.activate()
    entered, drained = asyncio.Event(), asyncio.Event()

    async def blocked_read(*args, **kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            drained.set()

    async def no_sleep(delay):
        return None

    value.camera.get_existing_photo.side_effect = blocked_read
    value.runtime._scheduler._sleep = no_sleep
    value.runtime._scheduler.submit(make_notice())
    await entered.wait()
    await value.runtime.async_close()
    assert drained.is_set()
    assert not value.coordinator._camera_refresh_lock.locked()
    assert value.runtime.diagnostics()["pending"] == 0
    assert value.runtime._scheduler._worker.done()
    assert not value.events


@pytest.mark.parametrize("result", [None, {"success": False, "images_saved": 1}])
async def test_incomplete_external_photo_is_consumed_without_listener_or_ready_event(
    runtime_factory, result
):
    value = runtime_factory()
    value.camera.get_existing_photo.return_value = result
    assert await value.runtime._verify(make_notice()) is True
    value.coordinator.async_update_listeners.assert_not_called()
    assert not value.events


@pytest.mark.parametrize("kind", ["photo_reported", "security_incident_reported"])
async def test_busy_alarm_operation_defers_reads_without_auth(runtime_factory, kind):
    value = runtime_factory()
    await value.operation.lock.acquire()
    try:
        assert await value.runtime._verify(make_notice(kind)) is False
        value.coordinator.async_login.assert_not_awaited()
        assert not value.events
    finally:
        value.operation.lock.release()


@pytest.mark.parametrize("kind", ["photo_reported", "security_incident_reported"])
async def test_unavailable_login_keeps_hint_pending_without_provider_query(
    runtime_factory, monkeypatch, kind
):
    value = runtime_factory()
    value.coordinator.async_login.return_value = False
    factory = Mock(side_effect=AssertionError("No query before login"))
    monkeypatch.setattr(notification_runtime, "NotificationClient", factory)
    assert await value.runtime._verify(make_notice(kind)) is False
    factory.assert_not_called()
    value.camera.get_existing_photo.assert_not_awaited()
    assert not value.events


@pytest.mark.parametrize("phase", ["context", "read"])
async def test_photo_operation_started_during_context_or_read_defers_publication(
    runtime_factory, phase
):
    value = runtime_factory()

    async def context():
        if phase == "context":
            await value.operation.lock.acquire()
        return "renewed-panel", "renewed-caps"

    async def read(*args, **kwargs):
        await value.operation.lock.acquire()
        return {"success": True, "images_saved": 3, "camera_identifier": "YR07"}

    value.coordinator._async_ensure_installation_context.side_effect = context
    value.camera.get_existing_photo.side_effect = read
    try:
        assert await value.runtime._verify(make_notice()) is False
        if phase == "context":
            value.camera.get_existing_photo.assert_not_awaited()
        assert not value.events
    finally:
        value.operation.lock.release()


async def test_malformed_device_metadata_is_skipped_without_authorizing_unknown_cameras(
    runtime_factory,
):
    value = runtime_factory()
    devices = value.coordinator.data["detailed_installation"]["installation"]["devices"]
    devices[:0] = [{}, {"type": "YR", "code": "bad"}, {"type": "DOOR", "code": "8"}]
    assert await value.runtime._verify(make_notice()) is True
    assert value.camera.get_existing_photo.await_args.kwargs[
        "expected_camera_codes"
    ] == ["YR07"]
    assert len(value.events) == 1


async def test_reconciled_recovery_seeds_baseline_without_creating_a_historical_event(
    runtime_factory,
):
    value = runtime_factory()
    snapshot = deepcopy(value.coordinator.data)
    snapshot["alarm_status"]["data"]["external"]["status"] = True
    value.coordinator.async_refresh_current_alarm_state.side_effect = [
        None,
        snapshot,
        snapshot,
        value.coordinator.data,
    ]
    notice = make_notice("alarm_operation_reported")
    recovery = replace(notice, event=replace(notice.event, delivery="reconciled"))
    assert await value.runtime._verify(recovery) is False
    assert await value.runtime._verify(recovery) is True
    assert not value.events
    assert await value.runtime._verify(notice) is True
    assert not value.events
    assert await value.runtime._verify(notice) is True
    assert len(value.events) == 1 and dict(value.events[0].facts)["external"] is False


async def test_command_result_is_correlated_without_extra_read_or_repeat(
    runtime_factory,
):
    value = runtime_factory()
    snapshot = deepcopy(value.coordinator.data)
    snapshot["alarm_status"]["data"]["external"]["status"] = True
    value.runtime.command_completed(snapshot, "synthetic-private-command")
    value.coordinator.async_refresh_current_alarm_state.assert_not_awaited()
    assert len(value.events) == 1
    event = value.events[0]
    assert event.verification == "command_result"
    assert dict(event.facts)["origin"] == "local_request"
    assert event.correlation_id != "synthetic-private-command"
    value.coordinator.async_refresh_current_alarm_state.return_value = snapshot
    assert await value.runtime._verify(make_notice("alarm_operation_reported")) is True
    assert len(value.events) == 1
    await value.runtime.async_close()
    value.runtime.command_completed(value.coordinator.data, "synthetic-after-close")
    assert len(value.events) == 1


async def test_authoritative_sync_time_ignores_unknown_snapshots(
    runtime_factory, monkeypatch
):
    value = runtime_factory()
    value.runtime.state_synchronized({})
    assert value.runtime.last_state_sync is None
    monkeypatch.setattr(notification_runtime.time, "time", lambda: 1700.0)
    value.runtime.state_synchronized(value.coordinator.data)
    assert value.runtime.last_state_sync == 1700.0
    value.runtime.state_synchronized({})
    assert value.runtime.last_state_sync == 1700.0


async def test_close_unhooks_local_photo_callback_and_disallows_late_events(
    runtime_factory,
):
    value = runtime_factory()
    old_callback = (
        value.coordinator.refresh_camera_images_use_case._photo_committed_callback
    )
    assert value.runtime.diagnostics() == {}
    value.runtime._photo_committed("YR08", 3, "unowned-signal")
    assert not value.events
    await value.runtime.async_close()
    assert (
        value.coordinator.refresh_camera_images_use_case._photo_committed_callback
        is None
    )
    old_callback("YR07", 3, "late-signal")
    value.runtime.activate()
    assert value.runtime._scheduler is None
    assert not value.events


async def test_runtime_supports_read_only_installations_without_capture_callback_port(
    runtime_factory,
):
    value = runtime_factory()
    value.coordinator.refresh_camera_images_use_case = object()
    runtime = notification_runtime.NotificationRuntime(value.coordinator, value.hub)
    runtime.activate()
    scheduler = runtime._scheduler
    runtime.activate()
    assert runtime._scheduler is scheduler
    assert await runtime._verify(make_notice()) is True
    await runtime.async_close()
    assert len(value.events) == 1

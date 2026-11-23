"""Focused tests for coordinator session and update error boundaries."""

from types import SimpleNamespace
import asyncio
from typing import Any, cast
from unittest.mock import AsyncMock, Mock, patch

import pytest
import jwt
from homeassistant.exceptions import ConfigEntryAuthFailed

from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.application.coordinator_authentication import (
    CoordinatorAuthenticationDecision,
)
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.models.alarm import ArmResult, DisarmResult
from custom_components.my_verisure.core.application.models.camera_refresh import CameraRefresh
from custom_components.my_verisure.core.application.coordinator_failure import (
    CoordinatorFailureClassifier,
)
from custom_components.my_verisure.core.application.coordinator_refresh_effects import (
    CoordinatorRefreshEffects,
)
from custom_components.my_verisure.core.application.coordinator_session_policy import (
    CoordinatorSessionPolicy,
)
from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureServiceBlockedError,
)


@pytest.fixture
def coordinator() -> MyVerisureDataUpdateCoordinator:
    value = object.__new__(MyVerisureDataUpdateCoordinator)
    value.installation_id = "home-1"
    value._dev_mode = False
    value.session_manager = Mock()
    value.session_manager.get_current_hash_token.return_value = "current-token"
    value._installation_auth_hash = "current-token"
    value._camera_refresh_lock = asyncio.Lock()
    value.file_manager = Mock()
    value.snapshot_store = Mock()
    value.refresh_effects = Mock(spec=CoordinatorRefreshEffects)
    value.refresh_effects.apply = AsyncMock()
    value.authentication_policy = Mock()
    value._failure_classifier = CoordinatorFailureClassifier()
    value.notifications = Mock()
    value.notifications.notify = AsyncMock()
    value.session_policy = CoordinatorSessionPolicy()
    value.authentication_policy.authenticate = AsyncMock(
        return_value=CoordinatorAuthenticationDecision(authenticated=True)
    )
    value.snapshot_service = Mock()
    value.create_dummy_camera_images_use_case = Mock()
    value.hass = cast(Any, SimpleNamespace(data={}))
    value.data = {}
    setattr(value, "load_alarm_info", Mock(return_value={}))
    setattr(value, "async_login", AsyncMock(return_value=True))
    object.__setattr__(value, "async_set_updated_data", Mock())
    return value


@pytest.mark.asyncio
async def test_update_data_returns_snapshot_and_persists_cache(coordinator) -> None:
    snapshot = {"installation_id": "home-1", "alarm_status": {"status": "armed"}}
    coordinator.snapshot_service.refresh = AsyncMock(return_value=snapshot)
    coordinator.snapshot_store.save = AsyncMock(return_value=True)
    coordinator.create_dummy_camera_images_use_case.create_dummy_camera_images = AsyncMock()

    coordinator.refresh_effects.apply = AsyncMock()

    await coordinator._async_update_data()

    coordinator.refresh_effects.apply.assert_awaited_once_with(
        snapshot,
        "home-1",
        create_dummy_images=True,
    )


@pytest.mark.asyncio
async def test_update_data_uses_cache_when_login_fails(coordinator) -> None:
    cached = {"installation_id": "home-1", "cached": True}
    setattr(coordinator, "async_login", AsyncMock(return_value=False))
    coordinator.authentication_policy.authenticate = AsyncMock(
        return_value=CoordinatorAuthenticationDecision(
            authenticated=False, cached_data=cached
        )
    )

    assert await coordinator._async_update_data() == cached


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error, expected",
    [
        (MyVerisureAuthenticationError("bad auth"), ConfigEntryAuthFailed),
        (MyVerisureConnectionError("offline"), MyVerisureError),
    ],
)
async def test_update_data_maps_provider_errors(coordinator, error, expected) -> None:
    coordinator.snapshot_service.refresh = AsyncMock(side_effect=error)

    with pytest.raises(expected):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_update_data_uses_cache_when_service_is_blocked(coordinator) -> None:
    cached = {"installation_id": "home-1", "cached": True}
    coordinator.snapshot_service.refresh = AsyncMock(
        side_effect=MyVerisureServiceBlockedError("blocked")
    )
    coordinator.load_alarm_info.return_value = cached
    coordinator.get_translation = AsyncMock(side_effect=lambda key: key)

    with patch("custom_components.my_verisure.coordinator.async_create") as notify:
        assert await coordinator._async_update_data() == cached

    coordinator.notifications.notify.assert_awaited_once_with(
        title_key="notifications.service.blocked.title",
        message_key="notifications.service.blocked.message",
        notification_id="verisure_service_blocked",
    )
    notify.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_camera_images_propagates_terminal_failure(coordinator) -> None:
    coordinator.coordinator_camera_refresh = Mock()
    coordinator.coordinator_camera_refresh.run = AsyncMock(
        side_effect=MyVerisureError("camera unavailable")
    )

    with pytest.raises(MyVerisureError):
        await coordinator.async_refresh_camera_images()


@pytest.mark.asyncio
async def test_manual_alarm_command_authenticates_before_provider_mutation(coordinator):
    order = []
    coordinator._panel_capabilities_from_stored_data = Mock(return_value=("panel", "caps"))
    coordinator.alarm_use_case = Mock()
    coordinator._async_refresh_alarm_only = AsyncMock()

    async def authenticate():
        order.append("authenticate")
        return True

    async def arm(*args, **kwargs):
        order.append("arm")
        return ArmResult(success=True, message="accepted")

    coordinator.async_login = AsyncMock(side_effect=authenticate)
    coordinator.alarm_use_case.arm_home = AsyncMock(side_effect=arm)

    assert (await coordinator.async_arm_home()).success
    assert order == ["authenticate", "arm"]


@pytest.mark.asyncio
async def test_manual_alarm_command_never_runs_after_rejected_authentication(coordinator):
    coordinator.async_login = AsyncMock(return_value=False)
    coordinator._panel_capabilities_from_stored_data = Mock(return_value=("panel", "caps"))
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.arm_home = AsyncMock()
    coordinator._async_refresh_alarm_only = AsyncMock()

    with pytest.raises(MyVerisureAuthenticationError):
        await coordinator.async_arm_home()

    coordinator.alarm_use_case.arm_home.assert_not_awaited()


@pytest.mark.asyncio
async def test_camera_refresh_never_runs_after_rejected_authentication(coordinator):
    coordinator.async_login = AsyncMock(return_value=False)
    coordinator.coordinator_camera_refresh = Mock()
    coordinator.coordinator_camera_refresh.run = AsyncMock()

    with pytest.raises(MyVerisureAuthenticationError):
        await coordinator.async_refresh_camera_images()

    coordinator.coordinator_camera_refresh.run.assert_not_awaited()


@pytest.mark.asyncio
async def test_overlapping_camera_refreshes_do_not_send_another_request(coordinator):
    started = asyncio.Event()

    async def pending(*args, **kwargs):
        started.set()
        await asyncio.Event().wait()

    coordinator.coordinator_camera_refresh = Mock(run=AsyncMock(side_effect=pending))
    first = asyncio.create_task(coordinator.async_refresh_camera_images())
    await started.wait()
    try:
        with pytest.raises(MyVerisureError, match="already running"):
            await coordinator.async_refresh_camera_images()
        assert coordinator.coordinator_camera_refresh.run.await_count == 1
    finally:
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
    assert not coordinator._camera_refresh_lock.locked()


@pytest.mark.asyncio
async def test_camera_refresh_reports_failed_photo_result_to_caller(coordinator):
    coordinator.coordinator_camera_refresh = Mock(
        run=AsyncMock(return_value=CameraRefresh([], 1, 0, 1, "2026-11-22T20:00:00Z"))
    )
    with pytest.raises(MyVerisureError, match="could not all be refreshed"):
        await coordinator.async_refresh_camera_images()


@pytest.mark.parametrize("code,external,night", [("D", False, False), ("E", True, False), ("Q", False, True), ("C", True, True)])
async def test_confirmed_command_updates_state_without_another_panel_request(coordinator, code, external, night):
    coordinator.data = {"detailed_installation": {"installation": {"panel": "panel"}}}
    coordinator._panel_capabilities_from_stored_data = Mock(return_value=("panel", "caps"))
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.arm_home = AsyncMock(return_value=ArmResult(True, "accepted", confirmed_state=code))
    coordinator._async_refresh_alarm_only = AsyncMock(side_effect=MyVerisureServiceBlockedError("extra request blocked"))

    result = await coordinator.async_arm_home()

    assert result.success
    coordinator._async_refresh_alarm_only.assert_not_awaited()
    snapshot = coordinator.refresh_effects.apply.await_args.args[0]
    assert snapshot["alarm_status"]["data"]["external"]["status"] is external
    assert snapshot["alarm_status"]["data"]["internal"]["night"]["status"] is night
    assert snapshot["alarm_status"]["data"]["internal"]["total"]["status"] is False


@pytest.mark.parametrize("code", [None, "UNRECOGNIZED"])
async def test_accepted_command_with_unknown_confirmation_invalidates_old_state(coordinator, code):
    coordinator.data = {"alarm_status": {"status": "OK"}, "detailed_installation": {}}
    coordinator._async_refresh_alarm_only = AsyncMock(side_effect=MyVerisureServiceBlockedError("read unavailable"))
    coordinator._panel_capabilities_from_stored_data = Mock(return_value=("panel", "caps"))
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.arm_home = AsyncMock(return_value=ArmResult(True, "accepted", confirmed_state=code))

    result = await coordinator.async_arm_home()

    snapshot = coordinator.refresh_effects.apply.await_args.args[0]
    assert snapshot["alarm_status"]["status"] is None
    assert snapshot["alarm_status"]["data"]["external"]["status"] is None
    assert result.success
    coordinator._async_refresh_alarm_only.assert_awaited_once()


async def test_unconfirmed_command_error_invalidates_old_state(coordinator):
    coordinator._panel_capabilities_from_stored_data = Mock(return_value=("panel", "caps"))
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.arm_home = AsyncMock(side_effect=MyVerisureServiceBlockedError("blocked"))

    with pytest.raises(MyVerisureServiceBlockedError):
        await coordinator.async_arm_home()

    snapshot = coordinator.refresh_effects.apply.await_args.args[0]
    assert snapshot["alarm_status"]["status"] is None


async def test_renewed_session_refreshes_installation_permissions_before_command(coordinator):
    order = []
    coordinator._installation_auth_hash = "previous-token"
    coordinator.data = {"detailed_installation": {"installation": {"panel": "old-panel", "capabilities": "old-caps"}}}
    detailed = Mock()
    detailed.installation.panel = "new-panel"
    detailed.installation.capabilities = "new-caps"
    detailed.dict.return_value = {"installation": {"panel": "new-panel", "capabilities": "new-caps"}}

    async def refresh_permissions(*args):
        order.append("permissions")
        return detailed

    async def disarm(*args, **kwargs):
        order.append("disarm")
        assert kwargs["panel"] == "new-panel"
        assert kwargs["capabilities"] == "new-caps"
        return DisarmResult(True, "confirmed", confirmed_state="D")

    coordinator.installation_use_case = Mock()
    coordinator.installation_use_case.get_installation_services = AsyncMock(side_effect=refresh_permissions)
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.disarm = AsyncMock(side_effect=disarm)

    assert (await coordinator.async_disarm()).success
    assert order == ["permissions", "disarm"]
    assert coordinator._installation_auth_hash == "current-token"


async def test_permission_refresh_failure_prevents_command(coordinator):
    coordinator._installation_auth_hash = "previous-token"
    coordinator.data = {"detailed_installation": {"installation": {"panel": "panel", "capabilities": "old-caps"}}}
    coordinator.installation_use_case = Mock()
    coordinator.installation_use_case.get_installation_services = AsyncMock(side_effect=MyVerisureConnectionError("offline"))
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.disarm = AsyncMock()

    with pytest.raises(MyVerisureConnectionError):
        await coordinator.async_disarm()

    coordinator.alarm_use_case.disarm.assert_not_awaited()
    assert coordinator._installation_auth_hash == "previous-token"


async def test_expired_capabilities_refresh_even_when_access_token_is_unchanged(coordinator):
    expired = jwt.encode({"exp": 1}, "synthetic-key-for-capabilities-expiry-tests", algorithm="HS256")
    coordinator.data = {"detailed_installation": {"installation": {"panel": "panel", "capabilities": expired}}}
    detailed = Mock()
    detailed.installation.panel = "panel"
    detailed.installation.capabilities = "fresh-caps"
    detailed.dict.return_value = {"installation": {"panel": "panel", "capabilities": "fresh-caps"}}
    coordinator.installation_use_case = Mock()
    coordinator.installation_use_case.get_installation_services = AsyncMock(return_value=detailed)

    assert await coordinator._async_ensure_installation_context() == ("panel", "fresh-caps")
    coordinator.installation_use_case.get_installation_services.assert_awaited_once_with("home-1")


async def test_context_cannot_bind_permissions_from_a_concurrently_replaced_session(coordinator):
    coordinator._installation_auth_hash = "previous-token"
    coordinator.data = {}
    detailed = Mock()
    detailed.installation.panel = "panel"
    detailed.installation.capabilities = "fresh-caps"

    async def change_session(*args):
        coordinator.session_manager.get_current_hash_token.return_value = "another-token"
        return detailed

    coordinator.installation_use_case = Mock()
    coordinator.installation_use_case.get_installation_services = AsyncMock(side_effect=change_session)
    coordinator.alarm_use_case = Mock()
    coordinator.alarm_use_case.disarm = AsyncMock()

    with pytest.raises(MyVerisureError, match="Session changed"):
        await coordinator.async_disarm()

    coordinator.alarm_use_case.disarm.assert_not_awaited()
    assert coordinator._installation_auth_hash == "previous-token"

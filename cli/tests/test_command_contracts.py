"""Exercise CLI behavior through real handlers and synthetic provider ports.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from cli.commands.alarm import AlarmCommand
from cli.commands.cameras import CameraCommand
from cli.commands.info import InfoCommand
from custom_components.my_verisure.core.application.models.alarm import AlarmStatus
from custom_components.my_verisure.core.application.models.camera_refresh import (
    CameraRefresh,
)
from custom_components.my_verisure.core.application.models.camera_refresh_data import (
    CameraRefreshData,
)
from custom_components.my_verisure.core.session_manager import SessionManager


def make_command(command_type):
    session = Mock(
        current_installation="synthetic-home",
        ensure_authenticated=AsyncMock(return_value=True),
        cleanup=AsyncMock(),
    )
    ports = {}

    def resolve(port):
        if port is SessionManager:
            return session
        return ports.setdefault(port, Mock())

    return command_type(composition_root=Mock(get=Mock(side_effect=resolve)))


def camera_result(successful, failed):
    return CameraRefresh(
        refresh_data=[
            CameraRefreshData(
                "2026-01-01T00:00:00+00:00",
                3 if index < successful else 0,
                f"YR{index:02d}",
            )
            for index in range(successful + failed)
        ],
        total_cameras=successful + failed,
        successful_refreshes=successful,
        failed_refreshes=failed,
        timestamp="2026-01-01T00:00:00+00:00",
    )


@pytest.mark.parametrize("action", ["refresh-images", "create-dummies"])
@pytest.mark.parametrize(("successful", "failed"), [(1, 0), (1, 1), (0, 1), (0, 0)])
async def test_camera_exit_status_reflects_failed_captures(action, successful, failed):
    command = make_command(CameraCommand)
    refresh = AsyncMock(return_value=camera_result(successful, failed))
    if action == "refresh-images":
        command.refresh_camera_images_use_case.refresh_camera_images = refresh
    else:
        command.create_dummy_camera_images_use_case.create_dummy_camera_images = refresh

    result = await command.execute(action, interactive=False)

    assert result is (failed == 0)
    assert refresh.await_args.kwargs["installation_id"] == "synthetic-home"


@pytest.mark.parametrize("command_type", [InfoCommand, AlarmCommand])
async def test_readonly_commands_preserve_noninteractive_auth(command_type):
    command = make_command(command_type)
    command.alarm_use_case.get_alarm_status = AsyncMock(
        return_value=AlarmStatus(success=True, message="ok", data={})
    )

    assert await command.execute("status", interactive=False) is True
    command.session_manager.ensure_authenticated.assert_awaited_once_with(False)


@pytest.mark.parametrize("command_type", [CameraCommand, InfoCommand, AlarmCommand])
async def test_noninteractive_multiple_installations_never_prompt(
    command_type, monkeypatch
):
    command = make_command(command_type)
    command.session_manager.current_installation = None
    command.installation_use_case.get_installations = AsyncMock(
        return_value=[
            SimpleNamespace(numinst="home-a"),
            SimpleNamespace(numinst="home-b"),
        ]
    )
    prompt = Mock(side_effect=AssertionError("batch mode must not read stdin"))
    monkeypatch.setattr("cli.commands.base.select_installation", prompt)
    action = "info" if command_type is CameraCommand else "status"

    assert await command.execute(action, interactive=False) is False
    prompt.assert_not_called()


@pytest.mark.parametrize("action", ["arm", "disarm"])
async def test_noninteractive_alarm_writes_require_explicit_confirmation(
    action, monkeypatch
):
    command = make_command(AlarmCommand)
    prompt = Mock(side_effect=AssertionError("batch mode must not read stdin"))
    monkeypatch.setattr("builtins.input", prompt)
    command.alarm_use_case.arm_home = AsyncMock()
    command.alarm_use_case.disarm = AsyncMock()
    kwargs = {"mode": "home"} if action == "arm" else {}

    assert (
        await command.execute(action, interactive=False, confirm=True, **kwargs)
        is False
    )
    prompt.assert_not_called()
    command.alarm_use_case.arm_home.assert_not_awaited()
    command.alarm_use_case.disarm.assert_not_awaited()


@pytest.mark.parametrize("action", ["info", "refresh-images", "create-dummies"])
@pytest.mark.parametrize("failure", ["auth", "installation", "provider"])
async def test_camera_failures_return_failure_without_sensitive_output(
    action, failure, capsys
):
    command = make_command(CameraCommand)
    if failure == "auth":
        command.session_manager.ensure_authenticated.return_value = False
    elif failure == "installation":
        command.session_manager.current_installation = None
        command.installation_use_case.get_installations = AsyncMock(return_value=[])
    else:
        error = RuntimeError("PRIVATE_PROVIDER_SENTINEL")
        command.get_installation_devices_use_case.get_installation_devices = AsyncMock(
            side_effect=error
        )
        command.refresh_camera_images_use_case.refresh_camera_images = AsyncMock(
            side_effect=error
        )
        command.create_dummy_camera_images_use_case.create_dummy_camera_images = (
            AsyncMock(side_effect=error)
        )

    assert await command.execute(action, interactive=False) is False
    assert "PRIVATE_PROVIDER_SENTINEL" not in capsys.readouterr().out


async def test_camera_listing_uses_the_shared_active_camera_policy(capsys):
    command = make_command(CameraCommand)
    command.get_installation_devices_use_case.get_installation_devices = AsyncMock(
        return_value=SimpleNamespace(
            devices=[
                SimpleNamespace(
                    type="YR", is_active=True, remote_use=True, serial_number=None
                ),
                SimpleNamespace(type="YP", is_active=False),
                SimpleNamespace(type="PIR", is_active=True),
            ]
        )
    )

    assert await command.execute("info", interactive=False) is True
    assert "Found 1 active camera devices" in capsys.readouterr().out

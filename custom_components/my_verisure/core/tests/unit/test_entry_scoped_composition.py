"""Tests for entry-scoped manager ownership in the composition root."""

from pathlib import Path

from custom_components.my_verisure.core.dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager
from custom_components.my_verisure.core.api.auth_client import AuthClient
from custom_components.my_verisure.core.api.installation_client import InstallationClient
from custom_components.my_verisure.core.api.alarm_client import AlarmClient
from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.api.device_manager import DeviceManager


def test_composition_root_owns_isolated_session_and_file_managers(tmp_path: Path):
    first_root = build_my_verisure_composition_root(
        session_file=tmp_path / "first-session.json",
        project_root=tmp_path / "first-project",
    )
    second_root = build_my_verisure_composition_root(
        session_file=tmp_path / "second-session.json",
        project_root=tmp_path / "second-project",
    )

    first_session = first_root.get(SessionManager)
    second_session = second_root.get(SessionManager)
    first_files = first_root.get(FileManager)
    second_files = second_root.get(FileManager)

    assert first_session is not second_session
    assert first_session.session_file != second_session.session_file
    assert first_files is not second_files
    assert first_files.get_project_root() != second_files.get_project_root()

    assert first_root.get(AuthClient)._resolve_session_manager() is first_session
    assert second_root.get(AuthClient)._resolve_session_manager() is second_session
    assert first_root.get(InstallationClient)._resolve_session_manager() is first_session
    assert first_root.get(AlarmClient)._resolve_session_manager() is first_session
    first_camera = first_root.get(CameraClient)
    assert first_camera._resolve_session_manager() is first_session
    assert first_camera._resolve_file_manager() is first_files
    assert second_root.get(InstallationClient)._resolve_session_manager() is second_session
    assert second_root.get(AlarmClient)._resolve_session_manager() is second_session
    second_camera = second_root.get(CameraClient)
    assert second_camera._resolve_session_manager() is second_session
    assert second_camera._resolve_file_manager() is second_files
    assert first_root.get(DeviceManager)._resolve_file_manager() is first_files
    assert second_root.get(DeviceManager)._resolve_file_manager() is second_files
    assert first_root.get(AuthClient)._device_manager is first_root.get(DeviceManager)
    assert second_root.get(AuthClient)._device_manager is second_root.get(DeviceManager)

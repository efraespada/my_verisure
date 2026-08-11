"""Tests for explicit dependency composition roots."""

from pathlib import Path

from ...api.alarm_client import AlarmClient
from ...api.auth_client import AuthClient
from ...api.camera_client import CameraClient
from ...api.installation_client import InstallationClient
from ...dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)
from ...file_manager import FileManager
from ...log_manager import LogManager
from ...config_manager import ConfigManager
from ...repositories.interfaces.installation_repository import InstallationRepository
from ...session_manager import SessionManager
from ...use_cases.interfaces.alarm_use_case import AlarmUseCase
from ...use_cases.interfaces.auth_use_case import AuthUseCase
from ...use_cases.interfaces.create_dummy_camera_images_use_case import (
    CreateDummyCameraImagesUseCase,
)
from ...use_cases.interfaces.get_installation_devices_use_case import (
    GetInstallationDevicesUseCase,
)
from ...use_cases.interfaces.installation_use_case import InstallationUseCase
from ...use_cases.interfaces.refresh_camera_images_use_case import (
    RefreshCameraImagesUseCase,
)


def test_composition_root_resolves_entry_scoped_graph(tmp_path: Path) -> None:
    """All application ports resolve from one explicit root."""
    root = build_my_verisure_composition_root(
        session_file=tmp_path / "session.json", project_root=tmp_path
    )

    assert isinstance(root.get(SessionManager), SessionManager)
    assert isinstance(root.get(FileManager), FileManager)
    assert isinstance(root.get(LogManager), LogManager)
    assert isinstance(root.get(ConfigManager), ConfigManager)
    assert isinstance(root.get(AuthClient), AuthClient)
    assert isinstance(root.get(InstallationClient), InstallationClient)
    assert isinstance(root.get(AlarmClient), AlarmClient)
    assert isinstance(root.get(CameraClient), CameraClient)
    assert isinstance(root.get(InstallationRepository), InstallationRepository)
    assert isinstance(root.get(AuthUseCase), AuthUseCase)
    assert isinstance(root.get(InstallationUseCase), InstallationUseCase)
    assert isinstance(root.get(AlarmUseCase), AlarmUseCase)
    assert isinstance(root.get(GetInstallationDevicesUseCase), GetInstallationDevicesUseCase)
    assert isinstance(root.get(RefreshCameraImagesUseCase), RefreshCameraImagesUseCase)
    assert isinstance(root.get(CreateDummyCameraImagesUseCase), CreateDummyCameraImagesUseCase)


def test_composition_root_reuses_owned_singletons(tmp_path: Path) -> None:
    """One root shares its owned session and file managers consistently."""
    root = build_my_verisure_composition_root(
        session_file=tmp_path / "session.json", project_root=tmp_path
    )

    session_manager = root.get(SessionManager)
    file_manager = root.get(FileManager)

    assert root.get(SessionManager) is session_manager
    assert root.get(FileManager) is file_manager
    assert root.get(AuthClient)._session_manager is session_manager
    assert root.get(InstallationClient)._session_manager is session_manager
    assert root.get(AlarmClient)._session_manager is session_manager
    assert root.get(CameraClient)._session_manager is session_manager
    assert root.get(LogManager)._file_manager is file_manager
    assert root.get(ConfigManager)._file_manager is file_manager


def test_composition_roots_are_isolated(tmp_path: Path) -> None:
    """Two entry roots never share sessions, files, clients, or repositories."""
    first_root = build_my_verisure_composition_root(
        session_file=tmp_path / "first" / "session.json",
        project_root=tmp_path / "first",
    )
    second_root = build_my_verisure_composition_root(
        session_file=tmp_path / "second" / "session.json",
        project_root=tmp_path / "second",
    )

    assert first_root.get(SessionManager) is not second_root.get(SessionManager)
    assert first_root.get(FileManager) is not second_root.get(FileManager)
    assert first_root.get(AuthClient) is not second_root.get(AuthClient)
    assert first_root.get(InstallationRepository) is not second_root.get(InstallationRepository)
    assert first_root.get(AuthUseCase) is not second_root.get(AuthUseCase)
    assert first_root.get(SessionManager).session_file != second_root.get(SessionManager).session_file
    assert first_root.get(FileManager)._project_root != second_root.get(FileManager)._project_root

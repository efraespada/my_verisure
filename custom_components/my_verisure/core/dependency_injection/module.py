"""Dependency injection module for My Verisure integration."""

import logging
from typing import Optional

from injector import Module, provider, singleton

from ..api.auth_client import AuthClient
from ..api.installation_client import InstallationClient
from ..api.alarm_client import AlarmClient
from ..api.camera_client import CameraClient
from ..repositories.interfaces.auth_repository import AuthRepository
from ..repositories.interfaces.installation_repository import InstallationRepository
from ..repositories.interfaces.alarm_repository import AlarmRepository
from ..repositories.interfaces.camera_repository import CameraRepository
from ..repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from ..repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
from ..repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
from ..repositories.implementations.camera_repository_impl import CameraRepositoryImpl
from ..use_cases.interfaces.auth_use_case import AuthUseCase
from ..use_cases.interfaces.installation_use_case import InstallationUseCase
from ..use_cases.interfaces.alarm_use_case import AlarmUseCase
from ..use_cases.interfaces.get_installation_devices_use_case import GetInstallationDevicesUseCase
from ..use_cases.interfaces.refresh_camera_images_use_case import RefreshCameraImagesUseCase
from ..use_cases.interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase
from ..use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from ..use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
from ..use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
from ..use_cases.implementations.get_installation_devices_use_case_impl import GetInstallationDevicesUseCaseImpl
from ..use_cases.implementations.refresh_camera_images_use_case_impl import RefreshCameraImagesUseCaseImpl
from ..use_cases.implementations.create_dummy_camera_images_use_case_impl import CreateDummyCameraImagesUseCaseImpl
from ..config_manager import ConfigManager
from ..log_manager import LogManager
from ..api.device_manager import DeviceManager
from ..file_manager import FileManager
from ..session_manager import SessionManager

logger = logging.getLogger(__name__)


class MyVerisureModule(Module):
    """My Verisure dependency injection module."""

    def __init__(
        self,
        session_manager: Optional[SessionManager] = None,
        file_manager: Optional[FileManager] = None,
    ) -> None:
        """Initialize the module with optional entry-scoped managers."""
        self._session_manager = session_manager
        self._file_manager = file_manager

    @singleton
    @provider
    def provide_session_manager(self) -> SessionManager:
        """Provide the session manager owned by this composition root."""
        return self._session_manager or SessionManager(
            file_manager=self.provide_file_manager()
        )

    @singleton
    @provider
    def provide_file_manager(self) -> FileManager:
        """Provide the file manager owned by this composition root."""
        return self._file_manager or FileManager()

    @singleton
    @provider
    def provide_log_manager(self, file_manager: FileManager) -> LogManager:
        """Provide LogManager with the graph-owned file manager."""
        return LogManager(file_manager=file_manager)

    @singleton
    @provider
    def provide_config_manager(self, file_manager: FileManager) -> ConfigManager:
        """Provide ConfigManager with the graph-owned file manager."""
        return ConfigManager(file_manager=file_manager)

    @singleton
    @provider
    def provide_device_manager(self, file_manager: FileManager) -> DeviceManager:
        """Provide DeviceManager with the graph-owned file manager."""
        return DeviceManager(file_manager=file_manager)

    @singleton
    @provider
    def provide_auth_client(
        self, session_manager: SessionManager, device_manager: DeviceManager
    ) -> AuthClient:
        """Provide AuthClient with graph-owned managers."""
        return AuthClient(
            session_manager=session_manager, device_manager=device_manager
        )


    @singleton
    @provider
    def provide_installation_client(
        self, session_manager: SessionManager
    ) -> InstallationClient:
        """Provide InstallationClient with the graph-owned session manager."""
        return InstallationClient(session_manager=session_manager)

    @singleton
    @provider
    def provide_alarm_client(self, session_manager: SessionManager) -> AlarmClient:
        """Provide AlarmClient with the graph-owned session manager."""
        return AlarmClient(session_manager=session_manager)

    @singleton
    @provider
    def provide_camera_client(
        self, session_manager: SessionManager, file_manager: FileManager
    ) -> CameraClient:
        """Provide CameraClient with graph-owned managers."""
        return CameraClient(
            session_manager=session_manager, file_manager=file_manager
        )

    @singleton
    @provider
    def provide_auth_repository(self, auth_client: AuthClient) -> AuthRepository:
        """Provide AuthRepository instance."""
        return AuthRepositoryImpl(auth_client)

    @singleton
    @provider
    def provide_installation_repository(
        self, installation_client: InstallationClient, file_manager: FileManager
    ) -> InstallationRepository:
        """Provide InstallationRepository with graph-owned file storage."""
        return InstallationRepositoryImpl(
            installation_client, file_manager=file_manager
        )

    @singleton
    @provider
    def provide_alarm_repository(self, alarm_client: AlarmClient) -> AlarmRepository:
        """Provide AlarmRepository instance."""
        return AlarmRepositoryImpl(alarm_client)

    @singleton
    @provider
    def provide_camera_repository(self, camera_client: CameraClient) -> CameraRepository:
        """Provide CameraRepository instance."""
        return CameraRepositoryImpl(camera_client)

    @singleton
    @provider
    def provide_auth_use_case(self, auth_repository: AuthRepository) -> AuthUseCase:
        """Provide AuthUseCase instance."""
        return AuthUseCaseImpl(auth_repository)

    @singleton
    @provider
    def provide_installation_use_case(self, installation_repository: InstallationRepository) -> InstallationUseCase:
        """Provide InstallationUseCase instance."""
        return InstallationUseCaseImpl(installation_repository)

    @singleton
    @provider
    def provide_alarm_use_case(self, alarm_repository: AlarmRepository, installation_repository: InstallationRepository) -> AlarmUseCase:
        """Provide AlarmUseCase instance."""
        return AlarmUseCaseImpl(alarm_repository, installation_repository)

    @singleton
    @provider
    def provide_get_installation_devices_use_case(self, installation_repository: InstallationRepository) -> GetInstallationDevicesUseCase:
        """Provide GetInstallationDevicesUseCase instance."""
        return GetInstallationDevicesUseCaseImpl(installation_repository)

    @singleton
    @provider
    def provide_refresh_camera_images_use_case(self, camera_repository: CameraRepository, installation_repository: InstallationRepository) -> RefreshCameraImagesUseCase:
        """Provide RefreshCameraImagesUseCase instance."""
        return RefreshCameraImagesUseCaseImpl(camera_repository, installation_repository)

    @singleton
    @provider
    def provide_create_dummy_camera_images_use_case(
        self,
        installation_repository: InstallationRepository,
        file_manager: FileManager,
    ) -> CreateDummyCameraImagesUseCase:
        """Provide dummy image use case with graph-owned file storage."""
        return CreateDummyCameraImagesUseCaseImpl(
            installation_repository, file_manager=file_manager
        )

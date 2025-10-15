"""Dependency injection module for My Verisure integration."""

import logging
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
from ..use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from ..use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
from ..use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
from ..use_cases.implementations.get_installation_devices_use_case_impl import GetInstallationDevicesUseCaseImpl
from ..use_cases.implementations.refresh_camera_images_use_case_impl import RefreshCameraImagesUseCaseImpl

logger = logging.getLogger(__name__)


class MyVerisureModule(Module):
    """My Verisure dependency injection module."""

    def __init__(self):
        """Initialize the module."""
        pass

    @singleton
    @provider
    def provide_auth_client(self) -> AuthClient:
        """Provide AuthClient instance."""
        return AuthClient()


    @singleton
    @provider
    def provide_installation_client(self) -> InstallationClient:
        """Provide InstallationClient instance."""
        return InstallationClient()

    @singleton
    @provider
    def provide_alarm_client(self) -> AlarmClient:
        """Provide AlarmClient instance."""
        return AlarmClient()

    @singleton
    @provider
    def provide_camera_client(self) -> CameraClient:
        """Provide CameraClient instance."""
        return CameraClient()

    @singleton
    @provider
    def provide_auth_repository(self, auth_client: AuthClient) -> AuthRepository:
        """Provide AuthRepository instance."""
        return AuthRepositoryImpl(auth_client)

    @singleton
    @provider
    def provide_installation_repository(self, installation_client: InstallationClient) -> InstallationRepository:
        """Provide InstallationRepository instance."""
        return InstallationRepositoryImpl(installation_client)

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

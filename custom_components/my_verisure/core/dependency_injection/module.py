"""Dependency injection module for My Verisure integration."""

import logging
from injector import Module, provider, singleton

from ..api.auth_client import AuthClient
from ..api.installation_client import InstallationClient
from ..api.alarm_client import AlarmClient
from ..repositories.interfaces.auth_repository import AuthRepository
from ..repositories.interfaces.installation_repository import InstallationRepository
from ..repositories.interfaces.alarm_repository import AlarmRepository
from ..repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from ..repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
from ..repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
from ..use_cases.interfaces.auth_use_case import AuthUseCase
from ..use_cases.interfaces.installation_use_case import InstallationUseCase
from ..use_cases.interfaces.alarm_use_case import AlarmUseCase
from ..use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from ..use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
from ..use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl

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

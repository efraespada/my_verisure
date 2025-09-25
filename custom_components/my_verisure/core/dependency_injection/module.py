"""Dependency injection module for My Verisure integration."""

import logging
from typing import Dict, Any
from injector import Module, provider, singleton

from ..api.auth_client import AuthClient
from ..api.session_client import SessionClient
from ..api.installation_client import InstallationClient
from ..api.alarm_client import AlarmClient
from ..repositories.interfaces.auth_repository import AuthRepository
from ..repositories.interfaces.session_repository import SessionRepository
from ..repositories.interfaces.installation_repository import InstallationRepository
from ..repositories.interfaces.alarm_repository import AlarmRepository
from ..repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from ..repositories.implementations.session_repository_impl import SessionRepositoryImpl
from ..repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
from ..repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
from ..use_cases.interfaces.auth_use_case import AuthUseCase
from ..use_cases.interfaces.session_use_case import SessionUseCase
from ..use_cases.interfaces.installation_use_case import InstallationUseCase
from ..use_cases.interfaces.alarm_use_case import AlarmUseCase
from ..use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from ..use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
from ..use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
from ..use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl

logger = logging.getLogger(__name__)


class MyVerisureModule(Module):
    """My Verisure dependency injection module."""

    def __init__(self, username: str = None, password: str = None, 
                 hash_token: str = None, session_data: Dict[str, Any] = None):
        """Initialize the module with session data."""
        self.username = username
        self.password = password
        self.hash_token = hash_token
        self.session_data = session_data or {}

    @singleton
    @provider
    def provide_auth_client(self) -> AuthClient:
        """Provide AuthClient instance."""
        return AuthClient(user=self.username, password=self.password)

    @singleton
    @provider
    def provide_session_client(self) -> SessionClient:
        """Provide SessionClient instance."""
        return SessionClient(user=self.username, hash_token=self.hash_token, session_data=self.session_data)

    @singleton
    @provider
    def provide_installation_client(self) -> InstallationClient:
        """Provide InstallationClient instance."""
        return InstallationClient(hash_token=self.hash_token, session_data=self.session_data)

    @singleton
    @provider
    def provide_alarm_client(self) -> AlarmClient:
        """Provide AlarmClient instance."""
        return AlarmClient(hash_token=self.hash_token, session_data=self.session_data)

    @singleton
    @provider
    def provide_auth_repository(self, auth_client: AuthClient) -> AuthRepository:
        """Provide AuthRepository instance."""
        return AuthRepositoryImpl(auth_client)

    @singleton
    @provider
    def provide_session_repository(self, session_client: SessionClient) -> SessionRepository:
        """Provide SessionRepository instance."""
        return SessionRepositoryImpl(session_client)

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
    def provide_session_use_case(self, session_repository: SessionRepository) -> SessionUseCase:
        """Provide SessionUseCase instance."""
        return SessionUseCaseImpl(session_repository)

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

"""Dependency injection providers for My Verisure integration."""

import logging
from typing import Optional

from .container import register_singleton, register
from api.client import MyVerisureClient
from repositories.interfaces.auth_repository import AuthRepository
from repositories.interfaces.session_repository import SessionRepository
from repositories.interfaces.installation_repository import InstallationRepository
from repositories.interfaces.alarm_repository import AlarmRepository
from repositories.implementations.auth_repository_impl import AuthRepositoryImpl
from repositories.implementations.session_repository_impl import SessionRepositoryImpl
from repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
from repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
from use_cases.interfaces.auth_use_case import AuthUseCase
from use_cases.interfaces.session_use_case import SessionUseCase
from use_cases.interfaces.installation_use_case import InstallationUseCase
from use_cases.interfaces.alarm_use_case import AlarmUseCase
from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
from use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl

_LOGGER = logging.getLogger(__name__)


def setup_dependencies(username: str, password: str) -> None:
    """Set up all dependencies for the My Verisure integration."""
    _LOGGER.info("Setting up My Verisure dependencies")
    
    # Create a single shared client instance
    shared_client = MyVerisureClient(user=username, password=password)
    
    # Register the shared client as a singleton
    def get_shared_client():
        return shared_client
    
    register_singleton(MyVerisureClient, get_shared_client)
    
    # Register repositories as singletons, all using the same shared client
    def create_auth_repository():
        return AuthRepositoryImpl(shared_client)
    
    def create_session_repository():
        return SessionRepositoryImpl(shared_client)
    
    def create_installation_repository():
        return InstallationRepositoryImpl(shared_client)
    
    def create_alarm_repository():
        return AlarmRepositoryImpl(shared_client)
    
    register_singleton(AuthRepository, create_auth_repository)
    register_singleton(SessionRepository, create_session_repository)
    register_singleton(InstallationRepository, create_installation_repository)
    register_singleton(AlarmRepository, create_alarm_repository)
    
    # Register use cases as singletons
    def create_auth_use_case():
        auth_repo = create_auth_repository()
        return AuthUseCaseImpl(auth_repo)
    
    def create_session_use_case():
        session_repo = create_session_repository()
        return SessionUseCaseImpl(session_repo)
    
    def create_installation_use_case():
        installation_repo = create_installation_repository()
        return InstallationUseCaseImpl(installation_repo)
    
    def create_alarm_use_case():
        alarm_repo = create_alarm_repository()
        return AlarmUseCaseImpl(alarm_repo)
    
    register_singleton(AuthUseCase, create_auth_use_case)
    register_singleton(SessionUseCase, create_session_use_case)
    register_singleton(InstallationUseCase, create_installation_use_case)
    register_singleton(AlarmUseCase, create_alarm_use_case)
    
    _LOGGER.info("My Verisure dependencies setup completed")


def get_auth_use_case() -> AuthUseCase:
    """Get the authentication use case."""
    from .container import resolve
    return resolve(AuthUseCase)


def get_session_use_case() -> SessionUseCase:
    """Get the session use case."""
    from .container import resolve
    return resolve(SessionUseCase)


def get_installation_use_case() -> InstallationUseCase:
    """Get the installation use case."""
    from .container import resolve
    return resolve(InstallationUseCase)


def get_alarm_use_case() -> AlarmUseCase:
    """Get the alarm use case."""
    from .container import resolve
    return resolve(AlarmUseCase)


def get_client() -> MyVerisureClient:
    """Get the API client."""
    from .container import resolve
    return resolve(MyVerisureClient)


def clear_dependencies() -> None:
    """Clear all registered dependencies."""
    from .container import get_container
    container = get_container()
    container.clear()
    _LOGGER.info("My Verisure dependencies cleared") 
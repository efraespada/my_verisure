"""Dependency injection providers for My Verisure integration."""

import logging
from typing import Dict, Any

from .container import register_singleton
from api.auth_client import AuthClient
from api.session_client import SessionClient
from api.installation_client import InstallationClient
from api.alarm_client import AlarmClient
from repositories.interfaces.auth_repository import AuthRepository
from repositories.interfaces.session_repository import SessionRepository
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from repositories.interfaces.alarm_repository import AlarmRepository
from repositories.implementations.auth_repository_impl import (
    AuthRepositoryImpl,
)
from repositories.implementations.session_repository_impl import (
    SessionRepositoryImpl,
)
from repositories.implementations.installation_repository_impl import (
    InstallationRepositoryImpl,
)
from repositories.implementations.alarm_repository_impl import (
    AlarmRepositoryImpl,
)
from use_cases.interfaces.auth_use_case import AuthUseCase
from use_cases.interfaces.session_use_case import SessionUseCase
from use_cases.interfaces.installation_use_case import InstallationUseCase
from use_cases.interfaces.alarm_use_case import AlarmUseCase
from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
from use_cases.implementations.installation_use_case_impl import (
    InstallationUseCaseImpl,
)
from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl

_LOGGER = logging.getLogger(__name__)


def setup_dependencies(username: str, password: str, hash_token: str = None, session_data: Dict[str, Any] = None) -> None:
    """Set up all dependencies for the My Verisure integration."""
    _LOGGER.info("Setting up My Verisure dependencies")

    # Create specific clients for each domain
    auth_client = AuthClient(user=username, password=password)
    session_client = SessionClient(user=username, hash_token=hash_token, session_data=session_data)
    installation_client = InstallationClient(hash_token=hash_token, session_data=session_data)
    alarm_client = AlarmClient(hash_token=hash_token, session_data=session_data)

    # Function to update auth tokens in all clients
    def update_auth_tokens(hash_token: str, session_data: Dict[str, Any]) -> None:
        """Update authentication tokens in all clients."""
        session_client.update_auth_token(hash_token, session_data)
        installation_client.update_auth_token(hash_token, session_data)
        alarm_client.update_auth_token(hash_token, session_data)
        _LOGGER.info("Auth tokens updated in all clients")

    # Store the update function in the auth client for later use
    auth_client._update_other_clients = update_auth_tokens

    # Register the specific clients as singletons
    def get_auth_client():
        return auth_client

    def get_session_client():
        return session_client

    def get_installation_client():
        return installation_client

    def get_alarm_client():
        return alarm_client

    register_singleton(AuthClient, get_auth_client)
    register_singleton(SessionClient, get_session_client)
    register_singleton(InstallationClient, get_installation_client)
    register_singleton(AlarmClient, get_alarm_client)

    # Register repositories as singletons, each using their specific client
    def create_auth_repository():
        return AuthRepositoryImpl(auth_client)

    def create_session_repository():
        return SessionRepositoryImpl(session_client)

    def create_installation_repository():
        return InstallationRepositoryImpl(installation_client)

    def create_alarm_repository():
        return AlarmRepositoryImpl(alarm_client)

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
        installation_repo = create_installation_repository()
        return AlarmUseCaseImpl(alarm_repo, installation_repo)

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


# Client getters for direct access if needed
def get_auth_client() -> AuthClient:
    """Get the authentication client."""
    from .container import resolve

    return resolve(AuthClient)


def get_session_client() -> SessionClient:
    """Get the session client."""
    from .container import resolve

    return resolve(SessionClient)


def get_installation_client() -> InstallationClient:
    """Get the installation client."""
    from .container import resolve

    return resolve(InstallationClient)


def get_alarm_client() -> AlarmClient:
    """Get the alarm client."""
    from .container import resolve

    return resolve(AlarmClient)


def clear_dependencies() -> None:
    """Clear all registered dependencies."""
    from .container import get_container

    container = get_container()
    container.clear()
    _LOGGER.info("My Verisure dependencies cleared")

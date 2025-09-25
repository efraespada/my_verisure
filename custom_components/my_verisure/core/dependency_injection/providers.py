"""Dependency injection providers for My Verisure integration."""

import logging
from typing import Dict, Any

from .container import setup_injector, get_dependency, clear_injector
from .module import MyVerisureModule
from ..api.auth_client import AuthClient
from ..api.session_client import SessionClient
from ..api.installation_client import InstallationClient
from ..api.alarm_client import AlarmClient
from ..repositories.interfaces.auth_repository import AuthRepository
from ..repositories.interfaces.session_repository import SessionRepository
from ..repositories.interfaces.installation_repository import InstallationRepository
from ..repositories.interfaces.alarm_repository import AlarmRepository
from ..use_cases.interfaces.auth_use_case import AuthUseCase
from ..use_cases.interfaces.session_use_case import SessionUseCase
from ..use_cases.interfaces.installation_use_case import InstallationUseCase
from ..use_cases.interfaces.alarm_use_case import AlarmUseCase

logger = logging.getLogger(__name__)


def setup_dependencies(username: str, password: str, hash_token: str = None, session_data: Dict[str, Any] = None) -> None:
    """Set up all dependencies for the My Verisure integration."""
    logger.info("Setting up My Verisure dependencies")
    
    module = MyVerisureModule(
        username=username,
        password=password,
        hash_token=hash_token,
        session_data=session_data
    )
    
    setup_injector(module)
    logger.info("My Verisure dependencies setup completed")


def get_auth_use_case() -> AuthUseCase:
    """Get the authentication use case."""
    return get_dependency(AuthUseCase)


def get_session_use_case() -> SessionUseCase:
    """Get the session use case."""
    return get_dependency(SessionUseCase)


def get_installation_use_case() -> InstallationUseCase:
    """Get the installation use case."""
    return get_dependency(InstallationUseCase)


def get_alarm_use_case() -> AlarmUseCase:
    """Get the alarm use case."""
    return get_dependency(AlarmUseCase)


def get_auth_client() -> AuthClient:
    """Get the authentication client."""
    return get_dependency(AuthClient)


def get_session_client() -> SessionClient:
    """Get the session client."""
    return get_dependency(SessionClient)


def get_installation_client() -> InstallationClient:
    """Get the installation client."""
    return get_dependency(InstallationClient)


def get_alarm_client() -> AlarmClient:
    """Get the alarm client."""
    return get_dependency(AlarmClient)


def clear_dependencies() -> None:
    """Clear all registered dependencies."""
    clear_injector()
    logger.info("My Verisure dependencies cleared")
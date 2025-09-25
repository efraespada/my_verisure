"""Repository interfaces for My Verisure integration."""

from .auth_repository import AuthRepository
from .installation_repository import InstallationRepository
from .alarm_repository import AlarmRepository
from .session_repository import SessionRepository

__all__ = [
    "AuthRepository",
    "InstallationRepository",
    "AlarmRepository",
    "SessionRepository",
]

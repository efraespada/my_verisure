"""Repository interfaces for My Verisure integration."""

from .auth_repository import AuthRepository
from .installation_repository import InstallationRepository
from .alarm_repository import AlarmRepository

__all__ = [
    "AuthRepository",
    "InstallationRepository",
    "AlarmRepository",
]

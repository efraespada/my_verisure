"""Repositories for My Verisure integration."""

from .interfaces.auth_repository import AuthRepository
from .interfaces.installation_repository import InstallationRepository
from .interfaces.alarm_repository import AlarmRepository

__all__ = [
    "AuthRepository",
    "InstallationRepository",
    "AlarmRepository",
]

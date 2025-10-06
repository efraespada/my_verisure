"""Use case interfaces for My Verisure integration."""

from .auth_use_case import AuthUseCase
from .installation_use_case import InstallationUseCase
from .alarm_use_case import AlarmUseCase

__all__ = [
    "AuthUseCase",
    "InstallationUseCase",
    "AlarmUseCase",
]

"""Domain models for My Verisure API."""

from .auth import Auth, AuthResult
from .installation import Installation, InstallationServices, InstallationsList
from .alarm import AlarmStatus, ArmResult, DisarmResult, ArmStatus, DisarmStatus, CheckAlarm
from .session import SessionData
from .service import Service

__all__ = [
    "Auth",
    "AuthResult", 
    "Installation",
    "InstallationServices",
    "InstallationsList",
    "AlarmStatus",
    "ArmResult",
    "DisarmResult",
    "ArmStatus",
    "DisarmStatus",
    "CheckAlarm",
    "SessionData",
    "Service"
] 
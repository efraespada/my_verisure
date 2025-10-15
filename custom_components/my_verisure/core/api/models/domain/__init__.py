"""Domain models for My Verisure API."""

from .auth import AuthResult, Phone, OTPData, Auth
from .installation import (
    Installation,
    InstallationServices,
    InstallationsList,
    Service as InstallationService,
)
from .alarm import (
    AlarmStatus,
    ArmResult,
    DisarmResult,
    ArmStatus,
    DisarmStatus,
    CheckAlarm,
)
from .session import SessionData, Session, DeviceIdentifiers
from .service import Service
from .camera_refresh_data import CameraRefreshData
from .camera_refresh import CameraRefresh

__all__ = [
    "Auth",
    "AuthResult",
    "Phone",
    "OTPData",
    "Installation",
    "InstallationServices",
    "InstallationsList",
    "InstallationService",
    "AlarmStatus",
    "ArmResult",
    "DisarmResult",
    "ArmStatus",
    "DisarmStatus",
    "CheckAlarm",
    "SessionData",
    "Session",
    "DeviceIdentifiers",
    "Service",
    "CameraRefreshData",
    "CameraRefresh",
]

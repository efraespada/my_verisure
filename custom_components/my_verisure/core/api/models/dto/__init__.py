"""Data Transfer Objects for My Verisure API."""

from .auth_dto import AuthDTO, PhoneDTO, OTPDataDTO
from .installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
    InstallationsListDTO,
)
from .alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    DisarmResultDTO,
    ArmStatusDTO,
    DisarmStatusDTO,
    CheckAlarmDTO,
)
from .session_dto import SessionDTO, DeviceIdentifiersDTO
from .service_dto import ServiceDTO

__all__ = [
    "AuthDTO",
    "PhoneDTO",
    "OTPDataDTO",
    "InstallationDTO",
    "InstallationServicesDTO",
    "InstallationsListDTO",
    "AlarmStatusDTO",
    "ArmResultDTO",
    "DisarmResultDTO",
    "ArmStatusDTO",
    "DisarmStatusDTO",
    "CheckAlarmDTO",
    "SessionDTO",
    "DeviceIdentifiersDTO",
    "ServiceDTO",
]

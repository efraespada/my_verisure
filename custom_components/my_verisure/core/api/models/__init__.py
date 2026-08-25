"""Models for My Verisure API."""

from .dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO
from .dto.installation_dto import (
    InstallationDTO,
    DetailedInstallationDTO,
    ServiceDTO,
    InstallationsListDTO,
)
from .dto.alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    DisarmResultDTO,
    ArmStatusDTO,
    DisarmStatusDTO,
    CheckAlarmDTO,
)
from .dto.session_dto import SessionDTO, DeviceIdentifiersDTO

__all__ = [
    # DTOs
    "AuthDTO",
    "OTPDataDTO",
    "PhoneDTO",
    "InstallationDTO",
    "DetailedInstallationDTO",
    "ServiceDTO",
    "InstallationsListDTO",
    "AlarmStatusDTO",
    "ArmResultDTO",
    "DisarmResultDTO",
    "ArmStatusDTO",
    "DisarmStatusDTO",
    "CheckAlarmDTO",
    "SessionDTO",
    "DeviceIdentifiersDTO",
]

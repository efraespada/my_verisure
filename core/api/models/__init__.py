"""Models for My Verisure API."""

from .dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO
from .dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
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

from .domain.auth import Auth, AuthResult, OTPData
from .domain.installation import (
    Installation,
    InstallationServices,
    Service,
    InstallationsList,
)
from .domain.alarm import (
    AlarmStatus,
    ArmResult,
    DisarmResult,
    ArmStatus,
    DisarmStatus,
    CheckAlarm,
)
from .domain.session import Session, DeviceIdentifiers

__all__ = [
    # DTOs
    "AuthDTO",
    "OTPDataDTO",
    "PhoneDTO",
    "InstallationDTO",
    "InstallationServicesDTO",
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
    # Domain Models
    "Auth",
    "AuthResult",
    "OTPData",
    "Installation",
    "InstallationServices",
    "Service",
    "InstallationsList",
    "AlarmStatus",
    "ArmResult",
    "DisarmResult",
    "ArmStatus",
    "DisarmStatus",
    "CheckAlarm",
    "Session",
    "DeviceIdentifiers",
]

"""Alarm domain models for My Verisure API."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from ..dto.alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    DisarmResultDTO,
    ArmStatusDTO as ArmStatusDTOType,
    DisarmStatusDTO as DisarmStatusDTOType,
    CheckAlarmDTO,
)


@dataclass
class ArmResult:
    """Arm result domain model."""

    success: bool
    message: str
    reference_id: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: ArmResultDTO) -> "ArmResult":
        """Create ArmResult from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            reference_id=dto.reference_id,
        )

    def to_dto(self) -> ArmResultDTO:
        """Convert to DTO."""
        return ArmResultDTO(
            res="OK" if self.success else "KO",
            msg=self.message,
            reference_id=self.reference_id,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DisarmResult:
    """Disarm result domain model."""

    success: bool
    message: str
    reference_id: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: DisarmResultDTO) -> "DisarmResult":
        """Create DisarmResult from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            reference_id=dto.reference_id,
        )

    def to_dto(self) -> DisarmResultDTO:
        """Convert to DTO."""
        return DisarmResultDTO(
            res="OK" if self.success else "KO",
            msg=self.message,
            reference_id=self.reference_id,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AlarmStatus:
    """Alarm status domain model."""

    success: bool
    message: str
    status: Optional[str] = None
    numinst: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    forced_armed: Optional[bool] = None

    @classmethod
    def from_dto(cls, dto: AlarmStatusDTO) -> "AlarmStatus":
        """Create AlarmStatus from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            status=dto.status,
            numinst=dto.numinst,
            protom_response=dto.protom_response,
            protom_response_date=dto.protom_response_date,
            forced_armed=dto.forced_armed,
        )

    def to_dto(self) -> AlarmStatusDTO:
        """Convert to DTO."""
        return AlarmStatusDTO(
            res="OK" if self.success else "KO",
            msg=self.message,
            status=self.status,
            numinst=self.numinst,
            protom_response=self.protom_response,
            protom_response_date=self.protom_response_date,
            forced_armed=self.forced_armed,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ArmStatus:
    """Arm status domain model."""

    success: bool
    message: str
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    smartlock_status: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dto(cls, dto: ArmStatusDTOType) -> "ArmStatus":
        """Create ArmStatus from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            status=dto.status,
            protom_response=dto.protom_response,
            protom_response_date=dto.protom_response_date,
            numinst=dto.numinst,
            request_id=dto.request_id,
            error=dto.error,
            smartlock_status=dto.smartlock_status,
        )

    def to_dto(self) -> ArmStatusDTOType:
        """Convert to DTO."""
        return ArmStatusDTOType(
            res="OK" if self.success else "KO",
            msg=self.message,
            status=self.status,
            protom_response=self.protom_response,
            protom_response_date=self.protom_response_date,
            numinst=self.numinst,
            request_id=self.request_id,
            error=self.error,
            smartlock_status=self.smartlock_status,
        )


@dataclass
class DisarmStatus:
    """Disarm status domain model."""

    success: bool
    message: str
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dto(cls, dto: DisarmStatusDTOType) -> "DisarmStatus":
        """Create DisarmStatus from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            status=dto.status,
            protom_response=dto.protom_response,
            protom_response_date=dto.protom_response_date,
            numinst=dto.numinst,
            request_id=dto.request_id,
            error=dto.error,
        )

    def to_dto(self) -> DisarmStatusDTOType:
        """Convert to DTO."""
        return DisarmStatusDTOType(
            res="OK" if self.success else "KO",
            msg=self.message,
            status=self.status,
            protom_response=self.protom_response,
            protom_response_date=self.protom_response_date,
            numinst=self.numinst,
            request_id=self.request_id,
            error=self.error,
        )


@dataclass
class CheckAlarm:
    """Check alarm domain model."""

    success: bool
    message: str
    reference_id: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: CheckAlarmDTO) -> "CheckAlarm":
        """Create CheckAlarm from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            reference_id=dto.reference_id,
        )

    def to_dto(self) -> CheckAlarmDTO:
        """Convert to DTO."""
        return CheckAlarmDTO(
            res="OK" if self.success else "KO",
            msg=self.message,
            reference_id=self.reference_id,
        )

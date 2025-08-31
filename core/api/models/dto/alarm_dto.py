"""Alarm DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ArmResultDTO:
    """Arm result DTO."""

    res: str
    msg: str
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArmResultDTO":
        """Create ArmResultDTO from dictionary."""
        return cls(
            res=data.get("res", ""),
            msg=data.get("msg", ""),
            reference_id=data.get("referenceId"),
        )


@dataclass
class DisarmResultDTO:
    """Disarm result DTO."""

    res: str
    msg: str
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisarmResultDTO":
        """Create DisarmResultDTO from dictionary."""
        return cls(
            res=data.get("res", ""),
            msg=data.get("msg", ""),
            reference_id=data.get("referenceId"),
        )


@dataclass
class AlarmStatusDTO:
    """Alarm status DTO."""

    res: str
    msg: str
    status: Optional[str] = None
    numinst: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    forced_armed: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlarmStatusDTO":
        """Create AlarmStatusDTO from dictionary."""
        return cls(
            res=data.get("res", ""),
            msg=data.get("msg", ""),
            status=data.get("status"),
            numinst=data.get("numinst"),
            protom_response=data.get("protomResponse"),
            protom_response_date=data.get("protomResponseDate"),
            forced_armed=data.get("forcedArmed"),
        )


@dataclass
class ArmStatusDTO:
    """Arm status response DTO."""

    res: str
    msg: str
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    smartlock_status: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArmStatusDTO":
        """Create ArmStatusDTO from dictionary."""
        return cls(
            res=data.get("res", ""),
            msg=data.get("msg", ""),
            status=data.get("status"),
            protom_response=data.get("protomResponse"),
            protom_response_date=data.get("protomResponseDate"),
            numinst=data.get("numinst"),
            request_id=data.get("requestId"),
            error=data.get("error"),
            smartlock_status=data.get("smartlockStatus"),
        )


@dataclass
class DisarmStatusDTO:
    """Disarm status response DTO."""

    res: str
    msg: str
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisarmStatusDTO":
        """Create DisarmStatusDTO from dictionary."""
        return cls(
            res=data.get("res", ""),
            msg=data.get("msg", ""),
            status=data.get("status"),
            protom_response=data.get("protomResponse"),
            protom_response_date=data.get("protomResponseDate"),
            numinst=data.get("numinst"),
            request_id=data.get("requestId"),
            error=data.get("error"),
        )


@dataclass
class CheckAlarmDTO:
    """Check alarm response DTO."""

    res: str
    msg: str
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckAlarmDTO":
        """Create CheckAlarmDTO from dictionary."""
        return cls(
            res=data.get("res", ""),
            msg=data.get("msg", ""),
            reference_id=data.get("referenceId"),
        )

"""Pure alarm domain models for My Verisure."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ArmResult:
    success: bool
    message: str
    reference_id: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DisarmResult:
    success: bool
    message: str
    reference_id: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AlarmStatus:
    success: bool
    message: str
    status: Optional[str] = None
    numinst: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    forced_armed: Optional[bool] = None
    data: Optional[Dict[str, Any]] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArmStatus:
    success: bool
    message: str
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    smartlock_status: Optional[Dict[str, Any]] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DisarmStatus:
    success: bool
    message: str
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CheckAlarm:
    success: bool
    message: str
    reference_id: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

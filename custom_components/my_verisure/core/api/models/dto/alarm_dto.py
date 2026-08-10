"""Alarm DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


def _result_dict(res: str, msg: Optional[str], reference_id: Optional[str]) -> Dict[str, Any]:
    return {"res": res, "msg": msg, "referenceId": reference_id}


@dataclass
class ArmResultDTO:
    res: str
    msg: Optional[str]
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArmResultDTO":
        return cls(data.get("res", ""), data.get("msg"), data.get("referenceId"))

    def to_dict(self) -> Dict[str, Any]:
        return _result_dict(self.res, self.msg, self.reference_id)


@dataclass
class DisarmResultDTO:
    res: str
    msg: Optional[str]
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisarmResultDTO":
        return cls(data.get("res", ""), data.get("msg"), data.get("referenceId"))

    def to_dict(self) -> Dict[str, Any]:
        return _result_dict(self.res, self.msg, self.reference_id)


@dataclass
class AlarmStatusDTO:
    res: str
    msg: Optional[str]
    status: Optional[str] = None
    numinst: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    forced_armed: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlarmStatusDTO":
        return cls(data.get("res", ""), data.get("msg"), data.get("status"), data.get("numinst"), data.get("protomResponse"), data.get("protomResponseDate"), data.get("forcedArmed"))

    def to_dict(self) -> Dict[str, Any]:
        return {"res": self.res, "msg": self.msg, "status": self.status, "numinst": self.numinst, "protomResponse": self.protom_response, "protomResponseDate": self.protom_response_date, "forcedArmed": self.forced_armed}


@dataclass
class ArmStatusDTO:
    res: str
    msg: Optional[str]
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None
    smartlock_status: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArmStatusDTO":
        return cls(data.get("res", ""), data.get("msg"), data.get("status"), data.get("protomResponse"), data.get("protomResponseDate"), data.get("numinst"), data.get("requestId"), data.get("error"), data.get("smartlockStatus"))

    def to_dict(self) -> Dict[str, Any]:
        return {"res": self.res, "msg": self.msg, "status": self.status, "protomResponse": self.protom_response, "protomResponseDate": self.protom_response_date, "numinst": self.numinst, "requestId": self.request_id, "error": self.error, "smartlockStatus": self.smartlock_status}


@dataclass
class DisarmStatusDTO:
    res: str
    msg: Optional[str]
    status: Optional[str] = None
    protom_response: Optional[str] = None
    protom_response_date: Optional[str] = None
    numinst: Optional[str] = None
    request_id: Optional[str] = None
    error: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DisarmStatusDTO":
        return cls(data.get("res", ""), data.get("msg"), data.get("status"), data.get("protomResponse"), data.get("protomResponseDate"), data.get("numinst"), data.get("requestId"), data.get("error"))

    def to_dict(self) -> Dict[str, Any]:
        return {"res": self.res, "msg": self.msg, "status": self.status, "protomResponse": self.protom_response, "protomResponseDate": self.protom_response_date, "numinst": self.numinst, "requestId": self.request_id, "error": self.error}


@dataclass
class CheckAlarmDTO:
    res: str
    msg: Optional[str]
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckAlarmDTO":
        return cls(data.get("res", ""), data.get("msg"), data.get("referenceId"))

    def to_dict(self) -> Dict[str, Any]:
        return _result_dict(self.res, self.msg, self.reference_id)

"""Authentication DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _required_string(data: Dict[str, Any], key: str, scope: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{scope} field required: {key}")
    return value


def _required_int(data: Dict[str, Any], key: str, scope: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{scope} field required: {key}")
    return value


@dataclass
class PhoneDTO:
    id: int
    phone: str
    record_id: Optional[int] = None
    otp_hash: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "PhoneDTO":
        return cls(
            _required_int(data, "id", "phone"),
            _required_string(data, "phone", "phone"),
            data.get("record_id"),
            data.get("otp_hash"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "phone": self.phone, "record_id": self.record_id, "otp_hash": self.otp_hash}


@dataclass
class OTPDataDTO:
    phones: List[PhoneDTO]
    otp_hash: str
    auth_code: Optional[str] = None
    auth_type: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OTPDataDTO":
        phones_data = data.get("phones")
        if not isinstance(phones_data, list):
            raise ValueError("otp phones required")
        if any(not isinstance(phone, dict) for phone in phones_data):
            raise ValueError("otp phones invalid")
        return cls(
            phones=[PhoneDTO.from_dict(phone) for phone in phones_data],
            otp_hash=_required_string(data, "otpHash", "otp"),
            auth_code=data.get("authCode"),
            auth_type=data.get("authType"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phones": [phone.to_dict() for phone in self.phones],
            "otpHash": self.otp_hash,
            "authCode": self.auth_code,
            "authType": self.auth_type,
        }


@dataclass
class AuthDTO:
    res: str
    msg: str
    hash: Optional[str] = None
    refresh_token: Optional[str] = None
    lang: Optional[str] = None
    legals: Optional[bool] = None
    change_password: Optional[bool] = None
    need_device_authorization: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthDTO":
        return cls(
            res=_required_string(data, "res", "auth"),
            msg=_required_string(data, "msg", "auth"),
            hash=data.get("hash"),
            refresh_token=data.get("refreshToken"),
            lang=data.get("lang"),
            legals=data.get("legals"),
            change_password=data.get("changePassword"),
            need_device_authorization=data.get("needDeviceAuthorization"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "res": self.res,
            "msg": self.msg,
            "hash": self.hash,
            "refreshToken": self.refresh_token,
            "lang": self.lang,
            "legals": self.legals,
            "changePassword": self.change_password,
            "needDeviceAuthorization": self.need_device_authorization,
        }

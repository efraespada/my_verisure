"""Authentication DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PhoneDTO:
    id: int
    phone: str
    record_id: Optional[int] = None
    otp_hash: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "PhoneDTO":
        return cls(data.get("id", 0), data.get("phone", ""), data.get("record_id"), data.get("otp_hash"))

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
        return cls(
            phones=[PhoneDTO.from_dict(phone) for phone in data.get("phones", [])],
            otp_hash=data.get("otpHash", ""),
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
            res=data.get("res", ""),
            msg=data.get("msg", ""),
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

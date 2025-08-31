"""Authentication DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class PhoneDTO:
    """Phone number DTO for OTP."""

    id: int
    phone: str


@dataclass
class OTPDataDTO:
    """OTP data DTO."""

    phones: List[PhoneDTO]
    otp_hash: str
    auth_code: Optional[str] = None
    auth_type: Optional[str] = None


@dataclass
class AuthDTO:
    """Authentication response DTO."""

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
        """Create AuthDTO from dictionary."""
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
        """Convert to dictionary."""
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

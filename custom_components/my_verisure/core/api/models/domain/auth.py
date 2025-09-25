"""Authentication domain models for My Verisure API."""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from ..dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO


@dataclass
class Phone:
    """Phone number domain model."""

    id: int
    phone: str

    @classmethod
    def from_dto(cls, dto: PhoneDTO) -> "Phone":
        """Create Phone from DTO."""
        return cls(
            id=dto.id,
            phone=dto.phone,
        )

    def to_dto(self) -> PhoneDTO:
        """Convert to DTO."""
        return PhoneDTO(
            id=self.id,
            phone=self.phone,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class OTPData:
    """OTP data domain model."""

    phones: List[Phone]
    otp_hash: str
    auth_code: Optional[str] = None
    auth_type: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: OTPDataDTO) -> "OTPData":
        """Create OTPData from DTO."""
        return cls(
            phones=[Phone.from_dto(p) for p in dto.phones],
            otp_hash=dto.otp_hash,
            auth_code=dto.auth_code,
            auth_type=dto.auth_type,
        )

    def to_dto(self) -> OTPDataDTO:
        """Convert to DTO."""
        return OTPDataDTO(
            phones=[p.to_dto() for p in self.phones],
            otp_hash=self.otp_hash,
            auth_code=self.auth_code,
            auth_type=self.auth_type,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AuthResult:
    """Authentication result domain model."""

    success: bool
    message: str
    hash: Optional[str] = None
    refresh_token: Optional[str] = None
    lang: Optional[str] = None
    legals: Optional[bool] = None
    change_password: Optional[bool] = None
    need_device_authorization: Optional[bool] = None

    @classmethod
    def from_dto(cls, dto: AuthDTO) -> "AuthResult":
        """Create AuthResult from DTO."""
        return cls(
            success=dto.res == "OK",
            message=dto.msg,
            hash=dto.hash,
            refresh_token=dto.refresh_token,
            lang=dto.lang,
            legals=dto.legals,
            change_password=dto.change_password,
            need_device_authorization=dto.need_device_authorization,
        )

    def to_dto(self) -> AuthDTO:
        """Convert to DTO."""
        return AuthDTO(
            res="OK" if self.success else "KO",
            msg=self.message,
            hash=self.hash,
            refresh_token=self.refresh_token,
            lang=self.lang,
            legals=self.legals,
            change_password=self.change_password,
            need_device_authorization=self.need_device_authorization,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Auth:
    """Authentication domain model."""

    username: str
    password: str

    def __post_init__(self):
        """Validate authentication data."""
        if not self.username:
            raise ValueError("Username is required")
        if not self.password:
            raise ValueError("Password is required")

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

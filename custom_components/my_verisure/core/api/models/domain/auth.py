"""Pure authentication domain models for My Verisure."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Phone:
    """A phone number available for an authentication challenge."""

    id: int
    phone: str

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OTPData:
    """Authentication challenge data held by the application."""

    phones: List[Phone]
    otp_hash: str
    auth_code: Optional[str] = None
    auth_type: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthResult:
    """Application result of an authentication operation."""

    success: bool
    message: str
    hash: Optional[str] = None
    refresh_token: Optional[str] = None
    lang: Optional[str] = None
    legals: Optional[bool] = None
    change_password: Optional[bool] = None
    need_device_authorization: Optional[bool] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Auth:
    """Credentials supplied to the authentication use case."""

    username: str
    password: str

    def __post_init__(self) -> None:
        if not self.username:
            raise ValueError("Username is required")
        if not self.password:
            raise ValueError("Password is required")

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

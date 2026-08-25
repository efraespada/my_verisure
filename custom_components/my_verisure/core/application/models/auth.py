"""Application authentication models independent of provider DTOs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Phone:
    """A phone destination available for an authentication challenge."""

    id: int
    phone: str
    record_id: int | None = None

    def dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OTPData:
    """Authentication challenge data held by the application."""

    phones: list[Phone]
    otp_hash: str
    auth_code: str | None = None
    auth_type: str | None = None

    def dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AuthResult:
    """Application result of an authentication operation."""

    success: bool
    message: str
    hash: str | None = None
    refresh_token: str | None = None
    lang: str | None = None
    legals: bool | None = None
    change_password: bool | None = None
    need_device_authorization: bool | None = None

    def dict(self) -> dict[str, Any]:
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

    def dict(self) -> dict[str, Any]:
        return asdict(self)

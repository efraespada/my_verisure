"""Pure session domain models."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DeviceIdentifiers:
    id_device: str
    uuid: str
    id_device_indigitall: str
    device_name: str
    device_brand: str
    device_os_version: str
    device_version: str
    device_type: Optional[str] = None
    device_resolution: Optional[str] = None
    generated_time: Optional[int] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionData:
    cookies: Dict[str, str]
    session_data: Dict[str, Any]
    user: str
    saved_time: int
    hash: Optional[str] = None
    device_identifiers: Optional[DeviceIdentifiers] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Session:
    user: str
    password: str

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

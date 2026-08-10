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
    device_type: str = ""
    device_resolution: str = ""
    generated_time: int = 0

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SessionData:
    cookies: Dict[str, str]
    session_data: Dict[str, Any]
    hash: Optional[str] = None
    user: str = ""
    device_identifiers: Optional[DeviceIdentifiers] = None
    saved_time: int = 0

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Session:
    user: str
    password: str

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

"""Pure installation domain models for My Verisure API."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from .device import Device


@dataclass(frozen=True)
class Service:
    id_service: str
    active: bool
    visible: bool
    bde: Optional[str] = None
    is_premium: Optional[bool] = None
    cod_oper: Optional[str] = None
    request: Optional[str] = None
    min_wrapper_version: Optional[str] = None
    unprotect_active: Optional[bool] = None
    unprotect_device_status: Optional[bool] = None
    inst_date: Optional[str] = None
    generic_config: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Installation:
    numinst: str
    alias: str
    panel: str
    type: str
    name: str
    surname: str
    address: str
    city: str
    postcode: str
    province: str
    email: str
    phone: str
    due: Optional[str] = None
    role: Optional[str] = None

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstallationData:
    numinst: str
    role: str
    alias: str
    status: str
    panel: str
    sim: str
    instIbs: str
    services: List[Service]
    devices: List[Device]
    configRepoUser: Optional[str] = None
    capabilities: Optional[str] = None


@dataclass(frozen=True)
class DetailedInstallation:
    installation: InstallationData
    language: str

    def dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstallationsList:
    installations: List[Installation]

    def dict(self) -> Dict[str, Any]:
        return asdict(self)

"""Installation DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from .device_dto import DeviceDTO

@dataclass
class ServiceDTO:
    """Service DTO."""

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceDTO":
        """Create ServiceDTO from dictionary."""
        return cls(
            id_service=data.get("idService", ""),
            active=data.get("active", False),
            visible=data.get("visible", False),
            bde=data.get("bde"),
            is_premium=data.get("isPremium"),
            cod_oper=data.get("codOper"),
            request=data.get("request"),
            min_wrapper_version=data.get("minWrapperVersion"),
            unprotect_active=data.get("unprotectActive"),
            unprotect_device_status=data.get("unprotectDeviceStatus"),
            inst_date=data.get("instDate"),
            generic_config=data.get("genericConfig"),
            attributes=data.get("attributes"),
        )


@dataclass
class InstallationDTO:
    """Installation DTO."""

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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationDTO":
        """Create InstallationDTO from dictionary."""
        return cls(
            numinst=data.get("numinst", ""),
            alias=data.get("alias", ""),
            panel=data.get("panel", ""),
            type=data.get("type", ""),
            name=data.get("name", ""),
            surname=data.get("surname", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            postcode=data.get("postcode", ""),
            province=data.get("province", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            due=data.get("due"),
            role=data.get("role"),
        )


@dataclass
class InstallationDataDTO:
    """Installation data DTO with strict typing."""
    
    numinst: str
    role: str
    alias: str
    status: str
    panel: str
    sim: str
    instIbs: str
    services: List[ServiceDTO]
    devices: List[DeviceDTO]
    configRepoUser: Optional[str] = None
    capabilities: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationDataDTO":
        """Create InstallationDataDTO from dictionary."""
        return cls(
            numinst=data.get("numinst", ""),
            role=data.get("role", ""),
            alias=data.get("alias", ""),
            status=data.get("status", ""),
            panel=data.get("panel", ""),
            sim=data.get("sim", ""),
            instIbs=data.get("instIbs", ""),
            services=[ServiceDTO.from_dict(s) for s in data.get("services", [])],
            devices=[DeviceDTO.from_dict(d) for d in data.get("devices", [])],
            configRepoUser=data.get("configRepoUser"),
            capabilities=data.get("capabilities"),
        )


@dataclass
class DetailedInstallationDTO:
    """Installation services response DTO with strict typing."""

    installation: InstallationDataDTO
    language: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetailedInstallationDTO":
        """Create DetailedInstallationDTO from dictionary."""
        return cls(
            installation=InstallationDataDTO.from_dict(data.get("installation", {})),
            language=data.get("language", ""),
        )


@dataclass
class InstallationsListDTO:
    """Installations list response DTO."""

    installations: List[InstallationDTO] = None

    def __post_init__(self):
        """Initialize installations list if None."""
        if self.installations is None:
            self.installations = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationsListDTO":
        """Create InstallationsListDTO from dictionary."""
        installations = []
        if "installations" in data:
            installations = [
                InstallationDTO.from_dict(i) for i in data["installations"]
            ]

        return cls(installations=installations)

"""Installation DTOs for My Verisure API."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, cast

from .device_dto import DeviceDTO


@dataclass
class ServiceDTO:
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
        return cls(data.get("idService", ""), data.get("active", False), data.get("visible", False), data.get("bde"), data.get("isPremium"), data.get("codOper"), data.get("request"), data.get("minWrapperVersion"), data.get("unprotectActive"), data.get("unprotectDeviceStatus"), data.get("instDate"), data.get("genericConfig"), data.get("attributes"))

    def to_dict(self) -> Dict[str, Any]:
        return {"idService": self.id_service, "active": self.active, "visible": self.visible, "bde": self.bde, "isPremium": self.is_premium, "codOper": self.cod_oper, "request": self.request, "minWrapperVersion": self.min_wrapper_version, "unprotectActive": self.unprotect_active, "unprotectDeviceStatus": self.unprotect_device_status, "instDate": self.inst_date, "genericConfig": self.generic_config, "attributes": self.attributes}


@dataclass
class InstallationDTO:
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
        return cls(
            cast(str, data.get("numinst")),
            cast(str, data.get("alias")),
            cast(str, data.get("panel")),
            cast(str, data.get("type")),
            cast(str, data.get("name")),
            cast(str, data.get("surname")),
            cast(str, data.get("address")),
            cast(str, data.get("city")),
            cast(str, data.get("postcode")),
            cast(str, data.get("province")),
            cast(str, data.get("email")),
            cast(str, data.get("phone")),
            data.get("due"),
            data.get("role"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"numinst": self.numinst, "alias": self.alias, "panel": self.panel, "type": self.type, "name": self.name, "surname": self.surname, "address": self.address, "city": self.city, "postcode": self.postcode, "province": self.province, "email": self.email, "phone": self.phone, "due": self.due, "role": self.role}


@dataclass
class InstallationDataDTO:
    numinst: str
    role: str
    alias: str
    status: str
    panel: str
    sim: str
    instIbs: str
    services: List[ServiceDTO]
    devices: List[DeviceDTO] = field(default_factory=list)
    configRepoUser: Optional[str] = None
    capabilities: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationDataDTO":
        return cls(data.get("numinst", ""), data.get("role", ""), data.get("alias", ""), data.get("status", ""), data.get("panel", ""), data.get("sim", ""), data.get("instIbs", ""), [ServiceDTO.from_dict(s) for s in data.get("services", [])], [DeviceDTO.from_dict(d) for d in data.get("devices", [])], data.get("configRepoUser"), data.get("capabilities"))

    def to_dict(self) -> Dict[str, Any]:
        return {"numinst": self.numinst, "role": self.role, "alias": self.alias, "status": self.status, "panel": self.panel, "sim": self.sim, "instIbs": self.instIbs, "services": [service.to_dict() for service in self.services], "devices": [device.dict() for device in self.devices], "configRepoUser": self.configRepoUser, "capabilities": self.capabilities}


@dataclass
class DetailedInstallationDTO:
    installation: InstallationDataDTO
    language: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetailedInstallationDTO":
        return cls(InstallationDataDTO.from_dict(data.get("installation", {})), data.get("language", ""))

    def to_dict(self) -> Dict[str, Any]:
        return {"installation": self.installation.to_dict(), "language": self.language}


@dataclass
class InstallationsListDTO:
    installations: List[InstallationDTO] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationsListDTO":
        return cls([InstallationDTO.from_dict(i) for i in data.get("installations", [])])

    def to_dict(self) -> Dict[str, Any]:
        return {"installations": [installation.to_dict() for installation in self.installations]}

"""Installation DTOs for My Verisure API."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .device_dto import DeviceDTO


def _required_string(data: Dict[str, Any], key: str) -> str:
    """Read one required provider string without fabricating a default."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"installation field required: {key}")
    return value


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
        id_service = data.get("idService")
        active = data.get("active")
        visible = data.get("visible")
        if not isinstance(id_service, str) or not id_service.strip():
            raise ValueError("service field required: idService")
        if not isinstance(active, bool) or not isinstance(visible, bool):
            raise ValueError("service field required: active/visible")
        return cls(
            id_service,
            active,
            visible,
            data.get("bde"),
            data.get("isPremium"),
            data.get("codOper"),
            data.get("request"),
            data.get("minWrapperVersion"),
            data.get("unprotectActive"),
            data.get("unprotectDeviceStatus"),
            data.get("instDate"),
            data.get("genericConfig"),
            data.get("attributes"),
        )

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
            _required_string(data, "numinst"),
            _required_string(data, "alias"),
            _required_string(data, "panel"),
            _required_string(data, "type"),
            _required_string(data, "name"),
            _required_string(data, "surname"),
            _required_string(data, "address"),
            _required_string(data, "city"),
            _required_string(data, "postcode"),
            _required_string(data, "province"),
            _required_string(data, "email"),
            _required_string(data, "phone"),
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
        services_data = data.get("services")
        if not isinstance(services_data, list):
            raise ValueError("installation services required")
        devices_data = data.get("devices")
        if not isinstance(devices_data, list):
            raise ValueError("installation devices required")
        if any(not isinstance(service, dict) for service in services_data):
            raise ValueError("installation services invalid")
        if any(not isinstance(device, dict) for device in devices_data):
            raise ValueError("installation devices invalid")
        return cls(
            _required_string(data, "numinst"),
            _required_string(data, "role"),
            _required_string(data, "alias"),
            _required_string(data, "status"),
            _required_string(data, "panel"),
            _required_string(data, "sim"),
            _required_string(data, "instIbs"),
            [ServiceDTO.from_dict(s) for s in services_data],
            [DeviceDTO.from_dict(d) for d in devices_data],
            data.get("configRepoUser"),
            data.get("capabilities"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"numinst": self.numinst, "role": self.role, "alias": self.alias, "status": self.status, "panel": self.panel, "sim": self.sim, "instIbs": self.instIbs, "services": [service.to_dict() for service in self.services], "devices": [device.dict() for device in self.devices], "configRepoUser": self.configRepoUser, "capabilities": self.capabilities}


@dataclass
class DetailedInstallationDTO:
    installation: InstallationDataDTO
    language: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DetailedInstallationDTO":
        language = _required_string(data, "language")
        installation_data = data.get("installation")
        if not isinstance(installation_data, dict):
            raise ValueError("installation data required")
        return cls(InstallationDataDTO.from_dict(installation_data), language)

    def to_dict(self) -> Dict[str, Any]:
        return {"installation": self.installation.to_dict(), "language": self.language}


@dataclass
class InstallationsListDTO:
    installations: List[InstallationDTO] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationsListDTO":
        installations = data.get("installations")
        if not isinstance(installations, list):
            raise ValueError("installations required")
        if any(not isinstance(item, dict) for item in installations):
            raise ValueError("installations invalid")
        return cls([InstallationDTO.from_dict(i) for i in installations])

    def to_dict(self) -> Dict[str, Any]:
        return {"installations": [installation.to_dict() for installation in self.installations]}

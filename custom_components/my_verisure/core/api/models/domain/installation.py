"""Installation domain models for My Verisure API."""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from ..dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
    ServiceDTO,
    InstallationsListDTO,
)


@dataclass
class Service:
    """Service domain model."""

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
    def from_dto(cls, dto: ServiceDTO) -> "Service":
        """Create Service from DTO."""
        return cls(
            id_service=dto.id_service,
            active=dto.active,
            visible=dto.visible,
            bde=dto.bde,
            is_premium=dto.is_premium,
            cod_oper=dto.cod_oper,
            request=dto.request,
            min_wrapper_version=dto.min_wrapper_version,
            unprotect_active=dto.unprotect_active,
            unprotect_device_status=dto.unprotect_device_status,
            inst_date=dto.inst_date,
            generic_config=dto.generic_config,
            attributes=dto.attributes,
        )

    def to_dto(self) -> ServiceDTO:
        """Convert to DTO."""
        return ServiceDTO(
            id_service=self.id_service,
            active=self.active,
            visible=self.visible,
            bde=self.bde,
            is_premium=self.is_premium,
            cod_oper=self.cod_oper,
            request=self.request,
            min_wrapper_version=self.min_wrapper_version,
            unprotect_active=self.unprotect_active,
            unprotect_device_status=self.unprotect_device_status,
            inst_date=self.inst_date,
            generic_config=self.generic_config,
            attributes=self.attributes,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Installation:
    """Installation domain model."""

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
    def from_dto(cls, dto: InstallationDTO) -> "Installation":
        """Create Installation from DTO."""
        return cls(
            numinst=dto.numinst,
            alias=dto.alias,
            panel=dto.panel,
            type=dto.type,
            name=dto.name,
            surname=dto.surname,
            address=dto.address,
            city=dto.city,
            postcode=dto.postcode,
            province=dto.province,
            email=dto.email,
            phone=dto.phone,
            due=dto.due,
            role=dto.role,
        )

    def to_dto(self) -> InstallationDTO:
        """Convert to DTO."""
        return InstallationDTO(
            numinst=self.numinst,
            alias=self.alias,
            panel=self.panel,
            type=self.type,
            name=self.name,
            surname=self.surname,
            address=self.address,
            city=self.city,
            postcode=self.postcode,
            province=self.province,
            email=self.email,
            phone=self.phone,
            due=self.due,
            role=self.role,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class InstallationServices:
    """Installation services domain model."""

    language: Optional[str] = None
    installation_data: Optional[Dict[str, Any]] = None
    services: List[Service] = None
    capabilities: Optional[str] = None

    def __post_init__(self):
        """Initialize services list if None."""
        if self.services is None:
            self.services = []

    @classmethod
    def from_dto(cls, dto: InstallationServicesDTO) -> "InstallationServices":
        """Create InstallationServices from DTO."""
        services = [Service.from_dto(s) for s in dto.services]

        # Extract capabilities from installation data if available
        capabilities = None
        if dto.installation and isinstance(dto.installation, dict):
            capabilities = dto.installation.get("capabilities")

        return cls(
            language=dto.language,
            installation_data=dto.installation,
            services=services,
            capabilities=capabilities,
        )

    def to_dto(self) -> InstallationServicesDTO:
        """Convert to DTO."""
        services = [s.to_dto() for s in self.services]

        # Update installation data with capabilities if available
        installation_data = self.installation_data or {}
        if self.capabilities:
            installation_data = installation_data.copy()
            installation_data["capabilities"] = self.capabilities

        return InstallationServicesDTO(
            language=self.language,
            installation=installation_data,
            services=services,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class InstallationsList:
    """Installations list domain model."""

    installations: List[Installation] = None

    def __post_init__(self):
        """Initialize installations list if None."""
        if self.installations is None:
            self.installations = []

    @classmethod
    def from_dto(cls, dto: InstallationsListDTO) -> "InstallationsList":
        """Create InstallationsList from DTO."""
        installations = [Installation.from_dto(i) for i in dto.installations]
        return cls(installations=installations)

    def to_dto(self) -> InstallationsListDTO:
        """Convert to DTO."""
        installations = [i.to_dto() for i in self.installations]
        return InstallationsListDTO(installations=installations)

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

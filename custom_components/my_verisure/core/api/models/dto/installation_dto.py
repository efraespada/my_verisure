"""Installation DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any


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
class InstallationServicesDTO:
    """Installation services response DTO."""

    language: Optional[str] = None
    installation: Optional[Dict[str, Any]] = None
    services: List[ServiceDTO] = None

    def __post_init__(self):
        """Initialize services list if None."""
        if self.services is None:
            self.services = []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InstallationServicesDTO":
        """Create InstallationServicesDTO from dictionary."""
        services = []

        # Handle different data structures
        if "installation" in data and "services" in data["installation"]:
            # GraphQL response structure
            services = [
                ServiceDTO.from_dict(s)
                for s in data["installation"]["services"]
            ]
            language = data.get("language")
            installation = data.get("installation")
        elif "services" in data and "installation" in data:
            # Client original structure - check if this is actually GraphQL response
            # Check if we have the GraphQL structure nested inside
            if "data" in data and "xSSrv" in data["data"]:
                # This is actually a GraphQL response wrapped in client structure
                graphql_data = data["data"]["xSSrv"]
                services = [
                    ServiceDTO.from_dict(s)
                    for s in graphql_data["installation"]["services"]
                ]
                language = graphql_data.get("language")
                installation = graphql_data.get("installation")
            else:
                # Client original structure
                services = [ServiceDTO.from_dict(s) for s in data["services"]]
                language = data.get("language")
                installation = data.get("installation")
        else:
            # Fallback
            language = data.get("language")
            installation = data.get("installation")

        return cls(
            language=language,
            installation=installation,
            services=services,
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

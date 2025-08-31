"""Session domain models for My Verisure API."""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from ..dto.session_dto import SessionDTO, DeviceIdentifiersDTO


@dataclass
class DeviceIdentifiers:
    """Device identifiers domain model."""

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

    @classmethod
    def from_dto(cls, dto: DeviceIdentifiersDTO) -> "DeviceIdentifiers":
        """Create DeviceIdentifiers from DTO."""
        return cls(
            id_device=dto.id_device,
            uuid=dto.uuid,
            id_device_indigitall=dto.id_device_indigitall,
            device_name=dto.device_name,
            device_brand=dto.device_brand,
            device_os_version=dto.device_os_version,
            device_version=dto.device_version,
            device_type=dto.device_type,
            device_resolution=dto.device_resolution,
            generated_time=dto.generated_time,
        )

    def to_dto(self) -> DeviceIdentifiersDTO:
        """Convert to DTO."""
        return DeviceIdentifiersDTO(
            id_device=self.id_device,
            uuid=self.uuid,
            id_device_indigitall=self.id_device_indigitall,
            device_name=self.device_name,
            device_brand=self.device_brand,
            device_os_version=self.device_os_version,
            device_version=self.device_version,
            device_type=self.device_type,
            device_resolution=self.device_resolution,
            generated_time=self.generated_time,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SessionData:
    """Session data domain model."""

    cookies: Dict[str, str]
    session_data: Dict[str, Any]
    hash: Optional[str] = None
    user: str = ""
    device_identifiers: Optional[DeviceIdentifiers] = None
    saved_time: int = 0

    @classmethod
    def from_dto(cls, dto: SessionDTO) -> "SessionData":
        """Create SessionData from DTO."""
        device_identifiers = None
        if dto.device_identifiers:
            device_identifiers = DeviceIdentifiers.from_dto(
                dto.device_identifiers
            )

        return cls(
            cookies=dto.cookies,
            session_data=dto.session_data,
            hash=dto.hash,
            user=dto.user,
            device_identifiers=device_identifiers,
            saved_time=dto.saved_time,
        )

    def to_dto(self) -> SessionDTO:
        """Convert to DTO."""
        device_identifiers = None
        if self.device_identifiers:
            device_identifiers = self.device_identifiers.to_dto()

        return SessionDTO(
            cookies=self.cookies,
            session_data=self.session_data,
            hash=self.hash,
            user=self.user,
            device_identifiers=device_identifiers,
            saved_time=self.saved_time,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Session:
    """Session domain model."""

    user: str
    password: str

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

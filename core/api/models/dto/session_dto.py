"""Session DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class DeviceIdentifiersDTO:
    """Device identifiers DTO."""

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
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceIdentifiersDTO":
        """Create DeviceIdentifiersDTO from dictionary."""
        return cls(
            id_device=data.get("idDevice", ""),
            uuid=data.get("uuid", ""),
            id_device_indigitall=data.get("idDeviceIndigitall", ""),
            device_name=data.get("deviceName", ""),
            device_brand=data.get("deviceBrand", ""),
            device_os_version=data.get("deviceOsVersion", ""),
            device_version=data.get("deviceVersion", ""),
            device_type=data.get("deviceType", ""),
            device_resolution=data.get("deviceResolution", ""),
            generated_time=data.get("generated_time", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "idDevice": self.id_device,
            "uuid": self.uuid,
            "idDeviceIndigitall": self.id_device_indigitall,
            "deviceName": self.device_name,
            "deviceBrand": self.device_brand,
            "deviceOsVersion": self.device_os_version,
            "deviceVersion": self.device_version,
            "deviceType": self.device_type,
            "deviceResolution": self.device_resolution,
            "generated_time": self.generated_time,
        }


@dataclass
class SessionDTO:
    """Session data DTO."""

    cookies: Dict[str, str]
    session_data: Dict[str, Any]
    hash: Optional[str] = None
    user: str = ""
    device_identifiers: Optional[DeviceIdentifiersDTO] = None
    saved_time: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionDTO":
        """Create SessionDTO from dictionary."""
        device_identifiers = None
        if "device_identifiers" in data:
            device_identifiers = DeviceIdentifiersDTO.from_dict(
                data["device_identifiers"]
            )

        return cls(
            cookies=data.get("cookies", {}),
            session_data=data.get("session_data", {}),
            hash=data.get("hash"),
            user=data.get("user", ""),
            device_identifiers=device_identifiers,
            saved_time=data.get("saved_time", 0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cookies": self.cookies,
            "session_data": self.session_data,
            "hash": self.hash,
            "user": self.user,
            "device_identifiers": (
                self.device_identifiers.to_dict()
                if self.device_identifiers
                else None
            ),
            "saved_time": self.saved_time,
        }

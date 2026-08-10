"""Session DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class DeviceIdentifiersDTO:
    id_device: Optional[str] = None
    uuid: Optional[str] = None
    id_device_indigitall: Optional[str] = None
    device_name: Optional[str] = None
    device_brand: Optional[str] = None
    device_os_version: Optional[str] = None
    device_version: Optional[str] = None
    device_type: Optional[str] = None
    device_resolution: Optional[str] = None
    generated_time: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceIdentifiersDTO":
        return cls(
            id_device=data.get("idDevice"),
            uuid=data.get("uuid"),
            id_device_indigitall=data.get("idDeviceIndigitall"),
            device_name=data.get("deviceName"),
            device_brand=data.get("deviceBrand"),
            device_os_version=data.get("deviceOsVersion"),
            device_version=data.get("deviceVersion"),
            device_type=data.get("deviceType"),
            device_resolution=data.get("deviceResolution"),
            generated_time=data.get("generated_time"),
        )

    def to_dict(self) -> Dict[str, Any]:
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
    cookies: Dict[str, str]
    session_data: Optional[Dict[str, Any]]
    hash: Optional[str] = None
    user: Optional[str] = None
    device_identifiers: Optional[DeviceIdentifiersDTO] = None
    saved_time: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionDTO":
        raw_device = data.get("device_identifiers")
        device_identifiers = (
            DeviceIdentifiersDTO.from_dict(raw_device)
            if raw_device is not None
            else None
        )
        return cls(
            cookies=data.get("cookies", {}),
            session_data=data.get("session_data"),
            hash=data.get("hash"),
            user=data.get("user"),
            device_identifiers=device_identifiers,
            saved_time=data.get("saved_time"),
        )

    def to_dict(self) -> Dict[str, Any]:
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

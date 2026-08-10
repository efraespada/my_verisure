"""Pure device domain models for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class DeviceConfigFlags:
    pin_code: Optional[bool] = None
    doorbell_button: Optional[bool] = None

    def dict(self) -> Dict[str, Any]:
        return {"pin_code": self.pin_code, "doorbell_button": self.doorbell_button}


@dataclass(frozen=True)
class DeviceConfig:
    flags: Optional[DeviceConfigFlags] = None

    def dict(self) -> Dict[str, Any]:
        return {"flags": self.flags.dict() if self.flags else {}}


@dataclass(frozen=True)
class Device:
    id: str
    code: str
    name: str
    type: str
    subtype: str
    remote_use: bool
    id_service: str
    is_active: bool
    serial_number: Optional[str] = None
    config: Optional[DeviceConfig] = None

    def dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "type": self.type,
            "subtype": self.subtype,
            "remote_use": self.remote_use,
            "id_service": self.id_service,
            "is_active": self.is_active,
            "serial_number": self.serial_number,
            "config": self.config.dict() if self.config else {},
        }

    @property
    def display_name(self) -> str:
        return self.name or f"{self.type} {self.code}"

    @property
    def is_remote_accessible(self) -> bool:
        return self.remote_use and self.is_active

    @property
    def device_type_description(self) -> str:
        type_mapping = {
            "PIR": "Motion Sensor",
            "DOOR": "Door Sensor",
            "WINDOW": "Window Sensor",
            "SMOKE": "Smoke Detector",
            "PANEL": "Control Panel",
            "SIREN": "Siren",
            "CAMERA": "Camera",
            "DOORBELL": "Doorbell",
        }
        return type_mapping.get(self.type, self.type)


@dataclass(frozen=True)
class DeviceList:
    result: str
    devices: List[Device]

    @property
    def active_devices(self) -> List[Device]:
        return [device for device in self.devices if device.is_active]

    @property
    def remote_devices(self) -> List[Device]:
        return [device for device in self.devices if device.is_remote_accessible]

    def get_devices_by_type(self, device_type: str) -> List[Device]:
        return [device for device in self.devices if device.type == device_type]

    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        return next((device for device in self.devices if device.id == device_id), None)

    def dict(self) -> Dict[str, Any]:
        return {"result": self.result, "devices": [device.dict() for device in self.devices]}

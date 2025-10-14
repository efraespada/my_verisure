"""Device domain model for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DeviceConfigFlags:
    """Device configuration flags domain model."""
    
    pin_code: Optional[bool] = None
    doorbell_button: Optional[bool] = None
    
    @classmethod
    def from_dto(cls, dto) -> "DeviceConfigFlags":
        """Create from DTO."""
        return cls(
            pin_code=dto.pin_code,
            doorbell_button=dto.doorbell_button,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pin_code": self.pin_code,
            "doorbell_button": self.doorbell_button,
        }


@dataclass
class DeviceConfig:
    """Device configuration domain model."""
    
    flags: Optional[DeviceConfigFlags] = None
    
    @classmethod
    def from_dto(cls, dto) -> "DeviceConfig":
        """Create from DTO."""
        flags = DeviceConfigFlags.from_dto(dto.flags) if dto.flags else None
        
        return cls(flags=flags)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "flags": self.flags.to_dict() if self.flags else {},
        }


@dataclass
class Device:
    """Device domain model for My Verisure API."""
    
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
    
    @classmethod
    def from_dto(cls, dto) -> "Device":
        """Create from DTO."""
        config = DeviceConfig.from_dto(dto.config) if dto.config else None
        
        return cls(
            id=dto.id,
            code=dto.code,
            name=dto.name,
            type=dto.type,
            subtype=dto.subtype,
            remote_use=dto.remote_use,
            id_service=dto.id_service,
            is_active=dto.is_active,
            serial_number=dto.serial_number,
            config=config,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
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
            "config": self.config.to_dict() if self.config else {},
        }
    
    @property
    def display_name(self) -> str:
        """Get display name for the device."""
        return self.name or f"{self.type} {self.code}"
    
    @property
    def is_remote_accessible(self) -> bool:
        """Check if device can be accessed remotely."""
        return self.remote_use and self.is_active
    
    @property
    def device_type_description(self) -> str:
        """Get human-readable device type description."""
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


@dataclass
class DeviceList:
    """Device list domain model for My Verisure API."""
    
    result: str
    devices: List[Device]
    
    @classmethod
    def from_dto(cls, dto) -> "DeviceList":
        """Create from DTO."""
        devices = [Device.from_dto(device_dto) for device_dto in dto.devices]
        
        return cls(
            result=dto.res,
            devices=devices,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result": self.result,
            "devices": [device.to_dict() for device in self.devices],
        }
    
    @property
    def active_devices(self) -> List[Device]:
        """Get only active devices."""
        return [device for device in self.devices if device.is_active]
    
    @property
    def remote_devices(self) -> List[Device]:
        """Get only remote accessible devices."""
        return [device for device in self.devices if device.is_remote_accessible]
    
    def get_devices_by_type(self, device_type: str) -> List[Device]:
        """Get devices filtered by type."""
        return [device for device in self.devices if device.type == device_type]
    
    def get_device_by_id(self, device_id: str) -> Optional[Device]:
        """Get device by ID."""
        return next((device for device in self.devices if device.id == device_id), None)

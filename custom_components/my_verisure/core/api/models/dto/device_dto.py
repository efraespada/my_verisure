"""Device DTO for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class DeviceConfigFlagsDTO:
    """Device configuration flags DTO."""
    
    pin_code: Optional[bool] = None
    doorbell_button: Optional[bool] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceConfigFlagsDTO":
        """Create from dictionary."""
        return cls(
            pin_code=data.get("pinCode"),
            doorbell_button=data.get("doorbellButton"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pinCode": self.pin_code,
            "doorbellButton": self.doorbell_button,
        }


@dataclass
class DeviceConfigDTO:
    """Device configuration DTO."""
    
    flags: Optional[DeviceConfigFlagsDTO] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceConfigDTO":
        """Create from dictionary."""
        flags_data = data.get("flags", {})
        flags = DeviceConfigFlagsDTO.from_dict(flags_data) if flags_data else None
        
        return cls(flags=flags)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "flags": self.flags.to_dict() if self.flags else {},
        }


@dataclass
class DeviceDTO:
    """Device DTO for My Verisure API."""
    
    id: str
    code: str
    name: str
    type: str
    subtype: str
    remote_use: bool
    id_service: str
    is_active: bool
    serial_number: Optional[str] = None
    config: Optional[DeviceConfigDTO] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceDTO":
        """Create from dictionary."""
        config_data = data.get("config", {})
        config = DeviceConfigDTO.from_dict(config_data) if config_data else None
        
        return cls(
            id=data.get("id", ""),
            code=data.get("code", ""),
            name=data.get("name", ""),
            type=data.get("type", ""),
            subtype=data.get("subtype", ""),
            remote_use=data.get("remoteUse", False),
            id_service=data.get("idService", ""),
            is_active=data.get("isActive", False),
            serial_number=data.get("serialNumber"),
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
            "remoteUse": self.remote_use,
            "idService": self.id_service,
            "isActive": self.is_active,
            "serialNumber": self.serial_number,
            "config": self.config.to_dict() if self.config else {},
        }


@dataclass
class DeviceListDTO:
    """Device list DTO for My Verisure API."""
    
    res: str
    devices: List[DeviceDTO]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceListDTO":
        """Create from dictionary."""
        devices_data = data.get("devices", [])
        devices = [DeviceDTO.from_dict(device) for device in devices_data]
        
        return cls(
            res=data.get("res", ""),
            devices=devices,
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "res": self.res,
            "devices": [device.to_dict() for device in self.devices],
        }

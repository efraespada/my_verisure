"""Device DTO for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _required_string(data: Dict[str, Any], key: str) -> str:
    """Read a required device field without an empty fallback."""
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"device field required: {key}")
    return value


def _required_bool(data: Dict[str, Any], key: str) -> bool:
    """Read a required device boolean without a false fallback."""
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"device field required: {key}")
    return value
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
    
    def dict(self) -> Dict[str, Any]:
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
        flags_data = data.get("flags")
        if flags_data is not None and not isinstance(flags_data, dict):
            raise ValueError("device flags invalid")
        flags = DeviceConfigFlagsDTO.from_dict(flags_data) if flags_data is not None else None
        
        return cls(flags=flags)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "flags": self.flags.dict() if self.flags else {},
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
        config_data = data.get("config")
        if config_data is not None and not isinstance(config_data, dict):
            raise ValueError("device config invalid")
        config = DeviceConfigDTO.from_dict(config_data) if config_data else None

        return cls(
            id=_required_string(data, "id"),
            code=_required_string(data, "code"),
            name=_required_string(data, "name"),
            type=_required_string(data, "type"),
            subtype=_required_string(data, "subtype"),
            remote_use=_required_bool(data, "remoteUse"),
            id_service=_required_string(data, "idService"),
            is_active=_required_bool(data, "isActive"),
            serial_number=data.get("serialNumber"),
            config=config,
        )
    
    def dict(self) -> Dict[str, Any]:
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
            "config": self.config.dict() if self.config else {},
        }


@dataclass
class DeviceListDTO:
    """Device list DTO for My Verisure API."""
    
    res: str
    devices: List[DeviceDTO]
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceListDTO":
        """Create from dictionary."""
        devices_data = data.get("devices")
        if not isinstance(devices_data, list):
            raise ValueError("device list required")
        if any(not isinstance(device, dict) for device in devices_data):
            raise ValueError("device list invalid")
        devices = [DeviceDTO.from_dict(device) for device in devices_data]

        res = _required_string(data, "res")
        return cls(res=res, devices=devices)
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "res": self.res,
            "devices": [device.dict() for device in self.devices],
        }

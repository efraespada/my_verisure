#!/usr/bin/env python3
"""
DTO for Service.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class ServiceDTO:
    """DTO for a service."""

    id_service: str
    active: bool
    visible: bool
    bde: bool
    is_premium: bool
    cod_oper: str
    request: str
    min_wrapper_version: str
    unprotect_active: bool
    unprotect_device_status: bool
    inst_date: str
    generic_config: Dict[str, Any]
    attributes: List[Dict[str, Any]]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceDTO":
        """Create ServiceDTO from dictionary."""
        return cls(
            id_service=data.get("idService", ""),
            active=data.get("active", False),
            visible=data.get("visible", False),
            bde=data.get("bde", False),
            is_premium=data.get("isPremium", False),
            cod_oper=data.get("codOper", ""),
            request=data.get("request", ""),
            min_wrapper_version=data.get("minWrapperVersion", ""),
            unprotect_active=data.get("unprotectActive", False),
            unprotect_device_status=data.get("unprotectDeviceStatus", False),
            inst_date=data.get("instDate", ""),
            generic_config=data.get("genericConfig", {}),
            attributes=data.get("attributes", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "idService": self.id_service,
            "active": self.active,
            "visible": self.visible,
            "bde": self.bde,
            "isPremium": self.is_premium,
            "codOper": self.cod_oper,
            "request": self.request,
            "minWrapperVersion": self.min_wrapper_version,
            "unprotectActive": self.unprotect_active,
            "unprotectDeviceStatus": self.unprotect_device_status,
            "instDate": self.inst_date,
            "genericConfig": self.generic_config,
            "attributes": self.attributes,
        }

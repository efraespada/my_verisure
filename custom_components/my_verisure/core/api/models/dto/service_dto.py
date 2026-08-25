#!/usr/bin/env python3
"""
DTO for Service.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

def _required_string(data: Dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"service field required: {key}")
    return value


def _required_bool(data: Dict[str, Any], key: str) -> bool:
    value = data.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"service field required: {key}")
    return value


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
        id_service = data.get("idService")
        active = data.get("active")
        visible = data.get("visible")
        if not isinstance(id_service, str) or not id_service.strip():
            raise ValueError("service field required: idService")
        if not isinstance(active, bool) or not isinstance(visible, bool):
            raise ValueError("service field required: active/visible")
        generic_config = data.get("genericConfig")
        attributes = data.get("attributes")
        if not isinstance(generic_config, dict) or not isinstance(attributes, list):
            raise ValueError("service field required: genericConfig/attributes")
        if any(not isinstance(item, dict) for item in attributes):
            raise ValueError("service attributes invalid")
        return cls(
            id_service=id_service,
            active=active,
            visible=visible,
            bde=_required_bool(data, "bde"),
            is_premium=_required_bool(data, "isPremium"),
            cod_oper=_required_string(data, "codOper"),
            request=_required_string(data, "request"),
            min_wrapper_version=_required_string(data, "minWrapperVersion"),
            unprotect_active=_required_bool(data, "unprotectActive"),
            unprotect_device_status=_required_bool(data, "unprotectDeviceStatus"),
            inst_date=_required_string(data, "instDate"),
            generic_config=generic_config,
            attributes=attributes,
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

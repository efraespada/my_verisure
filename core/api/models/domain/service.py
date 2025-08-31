#!/usr/bin/env python3
"""
Domain model for Service.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any


@dataclass
class Service:
    """Domain model for a service."""

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
    def from_dto(cls, dto) -> "Service":
        """Create Service from DTO."""
        return cls(
            id_service=dto.id_service,
            active=dto.active,
            visible=dto.visible,
            bde=dto.bde,
            is_premium=dto.is_premium,
            cod_oper=dto.cod_oper,
            request=dto.request,
            min_wrapper_version=dto.min_wrapper_version,
            unprotect_active=dto.unprotect_active,
            unprotect_device_status=dto.unprotect_device_status,
            inst_date=dto.inst_date,
            generic_config=dto.generic_config,
            attributes=dto.attributes,
        )

    def to_dto(self):
        """Convert to DTO."""
        from api.models.dto.service_dto import ServiceDTO

        return ServiceDTO(
            id_service=self.id_service,
            active=self.active,
            visible=self.visible,
            bde=self.bde,
            is_premium=self.is_premium,
            cod_oper=self.cod_oper,
            request=self.request,
            min_wrapper_version=self.min_wrapper_version,
            unprotect_active=self.unprotect_active,
            unprotect_device_status=self.unprotect_device_status,
            inst_date=self.inst_date,
            generic_config=self.generic_config,
            attributes=self.attributes,
        )

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

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

    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

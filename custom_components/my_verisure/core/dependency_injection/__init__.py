"""Dependency injection for My Verisure integration."""

from .container import get_injector, setup_injector, get_dependency, clear_injector
from .module import MyVerisureModule
from .providers import (
    setup_dependencies,
    clear_dependencies,
    get_auth_use_case,
    get_session_use_case,
    get_installation_use_case,
    get_alarm_use_case,
    get_auth_client,
    get_session_client,
    get_installation_client,
    get_alarm_client,
)

__all__ = [
    "get_injector",
    "setup_injector", 
    "get_dependency",
    "clear_injector",
    "MyVerisureModule",
    "setup_dependencies",
    "clear_dependencies",
    "get_auth_use_case",
    "get_session_use_case",
    "get_installation_use_case",
    "get_alarm_use_case",
    "get_auth_client",
    "get_session_client",
    "get_installation_client",
    "get_alarm_client",
]

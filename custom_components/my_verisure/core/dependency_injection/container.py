"""Dependency injection container using injector."""

import logging
from typing import Optional, Type, TypeVar
from injector import Injector, Module

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global injector instance
_injector: Optional[Injector] = None


def get_injector() -> Injector:
    """Get the global injector instance."""
    global _injector
    if _injector is None:
        raise RuntimeError("Injector not setup. Call setup_injector() first.")
    return _injector


def setup_injector(module: Module) -> None:
    """Setup the global injector with a module."""
    global _injector
    _injector = Injector([module])
    logger.info("Dependency injection setup completed")


def get_dependency(interface: Type[T]) -> T:
    """Get a dependency from the global injector."""
    return get_injector().get(interface)


def clear_injector() -> None:
    """Clear the global injector."""
    global _injector
    _injector = None
    logger.info("Dependency injection cleared")
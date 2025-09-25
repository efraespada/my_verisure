"""Dependency injection container for My Verisure integration."""

from .container import DependencyContainer
from .providers import setup_dependencies

__all__ = [
    "DependencyContainer",
    "setup_dependencies",
]

"""Explicit dependency composition for My Verisure integration."""

from .composition_root import CompositionRoot, build_my_verisure_composition_root
from .module import MyVerisureModule

__all__ = [
    "CompositionRoot",
    "build_my_verisure_composition_root",
    "MyVerisureModule",
]

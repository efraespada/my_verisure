"""Explicit dependency composition root."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from injector import Injector, Module

from ..file_manager import FileManager
from ..session_manager import SessionManager

T = TypeVar("T")


class CompositionRoot:
    """Own one isolated dependency graph for one application boundary."""

    def __init__(self, module: Module) -> None:
        """Build an isolated graph from the supplied module."""
        self._injector = Injector([module])

    def get(self, dependency: type[T]) -> T:
        """Resolve one dependency from this root."""
        return self._injector.get(dependency)


def build_my_verisure_composition_root(
    *,
    session_file: str | Path | None = None,
    project_root: Path | None = None,
) -> CompositionRoot:
    """Build the production graph for one integration entry."""
    from .module import MyVerisureModule

    return CompositionRoot(
        MyVerisureModule(
            session_manager=SessionManager(session_file),
            file_manager=FileManager(project_root),
        )
    )

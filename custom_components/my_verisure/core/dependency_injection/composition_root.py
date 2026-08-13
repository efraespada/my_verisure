"""Explicit dependency composition root."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from injector import Injector, Module

from ..file_manager import FileManager
from ..session_manager import SessionManager


class CompositionRoot:
    """Own one isolated dependency graph for one application boundary."""

    def __init__(self, module: Module) -> None:
        """Build an isolated graph from the supplied module."""
        self._injector = Injector([module])

    def get(self, dependency: type[Any]) -> Any:
        """Resolve a dependency at the dynamic Injector boundary.

        Injector resolves abstract application ports at runtime.  Keeping this
        dynamic typing confined to this facade prevents framework typing
        limitations from leaking into domain and adapter code.
        """
        return self._injector.get(dependency)


def build_my_verisure_composition_root(
    *,
    session_file: str | Path | None = None,
    project_root: Path | None = None,
) -> CompositionRoot:
    """Build the production graph for one integration entry."""
    from .module import MyVerisureModule

    file_manager = FileManager(project_root)
    session_manager = SessionManager(session_file, file_manager=file_manager)
    root = CompositionRoot(
        MyVerisureModule(
            session_manager=session_manager,
            file_manager=file_manager,
        )
    )

    from ..use_cases.interfaces.auth_use_case import AuthUseCase

    auth_use_case = root.get(AuthUseCase)
    session_manager.set_authenticator(auth_use_case.login)
    return root

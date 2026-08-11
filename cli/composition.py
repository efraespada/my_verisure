"""Composition root for the My Verisure CLI."""

from pathlib import Path

from custom_components.my_verisure.core.dependency_injection.composition_root import (
    CompositionRoot,
    build_my_verisure_composition_root,
)


def build_cli_composition_root() -> CompositionRoot:
    """Build one dependency graph for the lifetime of a CLI invocation."""
    state_root = Path.home() / ".my_verisure"
    return build_my_verisure_composition_root(
        session_file=state_root / "session.json",
        project_root=state_root,
    )

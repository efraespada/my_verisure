#!/usr/bin/env python3
"""Fail-fast checks for repository bootstrap architecture rules."""

from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_ROOTS = (
    ROOT / "custom_components" / "my_verisure",
    ROOT / "cli",
)
FORBIDDEN_GLOBAL_MANAGER_ACCESS = (
    "get_file_manager()",
    "get_session_manager()",
    "get_config_manager()",
    "get_log_manager()",
)


def _import_targets(node: ast.AST, package: tuple[str, ...]) -> list[str]:
    """Resolve absolute and relative imports, including from-parent aliases."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    prefix = package[: len(package) - node.level + 1] if node.level else ()
    base = ".".join((*prefix, *((node.module or "").split(".") if node.module else ())))
    return [base, *(f"{base}.{alias.name}" for alias in node.names)]


def check_imports(root: Path) -> list[str]:
    """Keep core HA-free and policies independent of concrete adapters."""
    errors: list[str] = []
    core = root / "custom_components" / "my_verisure" / "core"
    infrastructure = {
        "api",
        "dependency_injection",
        "file_manager",
        "session_manager",
        "config_manager",
        "log_manager",
        "coordinator_snapshot_store",
        "camera_placeholder_store",
    }
    frameworks = {
        "homeassistant", "aiohttp", "gql", "requests", "PIL", "injector",
        "probatio", "voluptuous",
    }
    for path in sorted(core.rglob("*.py")):
        relative = path.relative_to(core)
        if "tests" in relative.parts:
            continue
        package = path.relative_to(root).with_suffix("").parts[:-1]
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as error:
            errors.append(f"invalid Python: {path.relative_to(root)}:{error.lineno}")
            continue
        is_policy = relative.parts[0] in {"application", "use_cases"} or (
            relative.parts[:2] == ("repositories", "interfaces")
        )
        is_model = relative.parts[:2] == ("application", "models")
        for node in ast.walk(tree):
            targets = _import_targets(node, package)
            forbidden = False
            for target in targets:
                parts = target.split(".")
                if parts[0] == "homeassistant":
                    forbidden = True
                if is_policy and parts[0] in frameworks:
                    forbidden = True
                if is_model and parts[0] not in (
                    sys.stdlib_module_names | {"custom_components"}
                ):
                    forbidden = True
                if parts[:3] == ["custom_components", "my_verisure", "core"]:
                    inner = parts[3:]
                    if is_policy and inner and inner[0] in infrastructure:
                        forbidden = True
                    if is_policy and inner[:2] == ["repositories", "implementations"]:
                        forbidden = True
                    if is_model and inner[:2] != ["application", "models"]:
                        forbidden = True
            if forbidden:
                errors.append(
                    f"outward policy import: {path.relative_to(root)}:"
                    f"{node.lineno}"  # type: ignore[attr-defined]
                )
    return errors


def main() -> int:
    errors = check_imports(ROOT)

    required_paths = (
        ROOT / "cli",
        ROOT / "custom_components" / "my_verisure" / "core",
        ROOT / "custom_components" / "my_verisure" / "tests",
    )
    for path in required_paths:
        if not path.exists():
            errors.append(f"required path is missing: {path.relative_to(ROOT)}")

    bootstrap_files = [ROOT / "my_verisure_cli.py"]
    bootstrap_files.extend((ROOT / "cli").rglob("*.py"))
    for path in bootstrap_files:
        source = path.read_text(encoding="utf-8")
        if "sys.path.append" in source or "sys.path.insert" in source:
            errors.append(f"CLI mutates sys.path: {path.relative_to(ROOT)}")
        if "from core " in source or "from core." in source:
            errors.append(
                "CLI imports the legacy top-level core package: "
                f"{path.relative_to(ROOT)}"
            )

    for production_root in PRODUCTION_ROOTS:
        for path in production_root.rglob("*.py"):
            if "/tests/" in path.as_posix():
                continue
            source = path.read_text(encoding="utf-8")
            for forbidden_access in FORBIDDEN_GLOBAL_MANAGER_ACCESS:
                if forbidden_access in source:
                    errors.append(
                        "production code uses global manager accessor "
                        f"{forbidden_access}: {path.relative_to(ROOT)}"
                    )
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts or ".hermes" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        if "singleton accessor `get_session_manager()`" in source:
            errors.append(
                "documentation describes the removed global session architecture: "
                f"{path.relative_to(ROOT)}"
            )

    if errors:
        print("ARCHITECTURE_GUARD_FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print("ARCHITECTURE_GUARD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

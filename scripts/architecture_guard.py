#!/usr/bin/env python3
"""Fail-fast checks for repository bootstrap architecture rules."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []

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


    pure_domain_models = (
        "auth.py",
        "alarm.py",
        "camera_request_image.py",
        "session.py",
        "device.py",
        "installation.py",
    )
    domain_root = (
        ROOT / "custom_components" / "my_verisure" / "core" / "api" / "models" / "domain"
    )
    for filename in pure_domain_models:
        path = domain_root / filename
        source = path.read_text(encoding="utf-8")
        if "models.dto" in source or "..dto" in source:
            errors.append(f"pure domain model imports DTOs: {path.relative_to(ROOT)}")

    if errors:
        print("ARCHITECTURE_GUARD_FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print("ARCHITECTURE_GUARD_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

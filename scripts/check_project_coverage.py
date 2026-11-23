"""Enforce measured production coverage without hiding the CLI or tooling.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
# Floors preserve the audited baseline; they do not claim exhaustive coverage.
FLOORS = {
    "custom_components/my_verisure": (85.0, 75.9),
    "cli": (73.0, 60.0),
    "scripts": (77.0, 69.0),
}
COMPLETE_MODULES = (
    "core/application/camera_placeholders.py",
    "core/application/polling.py",
    "core/camera_placeholder_store.py",
    "core/camera_image_sanitizer.py",
    "core/use_cases/implementations/create_dummy_camera_images_use_case_impl.py",
    "core/utils/jwt_utils.py",
)


def check_coverage(report: dict[str, Any], root: Path = ROOT) -> list[str]:
    """Require branch data, every production file and each scope's baseline."""
    errors: list[str] = []
    if report.get("meta", {}).get("branch_coverage") is not True:
        return ["branch measurement is required"]
    files = report.get("files", {})
    for module in COMPLETE_MODULES:
        name = f"custom_components/my_verisure/{module}"
        result = files.get(name)
        if result is None or result["missing_lines"] or result["missing_branches"]:
            errors.append(f"{name}: complete executable line/branch coverage required")
    for scope, (line_floor, branch_floor) in FLOORS.items():
        expected = {
            path.relative_to(root).as_posix()
            for path in (root / scope).rglob("*.py")
            if "tests" not in path.relative_to(root / scope).parts
            and path.name != "conftest.py"
        }
        missing = sorted(expected - files.keys())
        if missing:
            errors.append(
                f"{scope}: files missing from measurement: {', '.join(missing)}"
            )
            continue
        if not expected:
            errors.append(f"{scope}: production source is missing")
            continue
        covered_lines = statements = covered_branches = branches = 0
        for name in expected:
            summary = files[name]["summary"]
            covered_lines += summary["covered_lines"]
            statements += summary["num_statements"]
            covered_branches += summary["covered_branches"]
            branches += summary["num_branches"]
        line_percentage = 100 * covered_lines / statements if statements else 0
        branch_percentage = 100 * covered_branches / branches if branches else 0
        if line_percentage < line_floor or branch_percentage < branch_floor:
            errors.append(
                f"{scope}: {line_percentage:.2f}% lines / "
                f"{branch_percentage:.2f}% branches, required "
                f"{line_floor:g}% / {branch_floor:g}%"
            )
    return errors


def main() -> int:
    try:
        report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        errors = check_coverage(report)
    except (IndexError, OSError, ValueError, KeyError, TypeError, AttributeError):
        print("PROJECT_COVERAGE_FAILED: invalid or missing report", file=sys.stderr)
        return 1
    if errors:
        print("PROJECT_COVERAGE_FAILED: " + "; ".join(errors), file=sys.stderr)
        return 1
    print("PROJECT_COVERAGE_OK: integration, CLI and tooling baselines preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

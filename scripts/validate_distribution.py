"""Validate the Home Assistant integration artifact delivered to users."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "my_verisure"
REQUIRED = {
    "__init__.py",
    "manifest.json",
    "config_flow.py",
    "integration.py",
    "strings.json",
}
FORBIDDEN_PARTS = {
    ".coverage",
    ".pytest_cache",
    "__pycache__",
    "coverage.xml",
    "device_identifiers.json",
}


def load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / name for name in result.stdout.decode().split("\0") if name]


def validate_tree() -> None:
    if not INTEGRATION.is_dir():
        raise ValueError(f"Missing integration directory: {INTEGRATION}")
    missing = sorted(name for name in REQUIRED if not (INTEGRATION / name).is_file())
    if missing:
        raise ValueError(f"Missing required integration files: {', '.join(missing)}")

    manifest = load_json(INTEGRATION / "manifest.json")
    if manifest.get("domain") != "my_verisure":
        raise ValueError("manifest.json has an unexpected domain")
    if manifest.get("config_flow") is not True:
        raise ValueError("manifest.json must enable config_flow")
    if not isinstance(manifest.get("version"), str):
        raise ValueError("manifest.json must declare a string version")

    hacs = load_json(ROOT / "hacs.json")
    if hacs.get("filename") != "my_verisure":
        raise ValueError("hacs.json must point to the my_verisure integration")
    if "icon" in hacs:
        raise ValueError("hacs.json contains the unsupported icon key")

    forbidden = sorted(
        str(path.relative_to(ROOT))
        for path in tracked_files()
        if any(part in FORBIDDEN_PARTS for part in path.parts)
    )
    if forbidden:
        raise ValueError(f"Generated artifacts are tracked in the tree: {forbidden}")


def create_and_validate_zip() -> Path:
    artifact = ROOT / "dist" / "my_verisure.zip"
    artifact.parent.mkdir(exist_ok=True)
    with ZipFile(artifact, "w", ZIP_DEFLATED) as archive:
        for path in sorted(tracked_files()):
            if INTEGRATION not in path.parents:
                continue
            if path.is_file() and not any(part in FORBIDDEN_PARTS for part in path.parts):
                archive.write(path, Path("custom_components/my_verisure") / path.relative_to(INTEGRATION))

    with ZipFile(artifact) as archive:
        names = set(archive.namelist())
        expected = {f"custom_components/my_verisure/{name}" for name in REQUIRED}
        missing = sorted(expected - names)
        if missing:
            raise ValueError(f"ZIP is missing required files: {', '.join(missing)}")
        forbidden = sorted(name for name in names if any(part in FORBIDDEN_PARTS for part in Path(name).parts))
        if forbidden:
            raise ValueError(f"ZIP contains generated artifacts: {forbidden}")
    return artifact


def main() -> int:
    try:
        validate_tree()
        artifact = create_and_validate_zip()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"DISTRIBUTION_VALIDATION_FAILED: {error}", file=sys.stderr)
        return 1
    print(f"DISTRIBUTION_VALIDATION_OK: {artifact.relative_to(ROOT)}")
    artifact.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
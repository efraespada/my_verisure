"""Export installed default runtime dependency versions, without private paths.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from importlib.metadata import distribution
import json
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]


def runtime_requirements(requirements: list[str]) -> list[str]:
    """Walk the installed default dependency graph, not the whole HA environment."""
    pending = list(requirements)
    versions: dict[str, str] = {}
    while pending:
        requirement = Requirement(pending.pop())
        if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
            continue
        if requirement.extras:
            raise ValueError("Explicit extras need an expanded audit contract")
        name = canonicalize_name(requirement.name)
        if name in versions:
            continue
        package = distribution(requirement.name)
        versions[name] = package.version
        pending.extend(package.requires or [])
    return [f"{name}=={version}" for name, version in sorted(versions.items())]


def main() -> None:
    manifest = json.loads(
        (ROOT / "custom_components/my_verisure/manifest.json").read_text()
    )
    print("\n".join(runtime_requirements(manifest["requirements"])))


if __name__ == "__main__":
    main()

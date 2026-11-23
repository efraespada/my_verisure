"""Check local Markdown file links and SDD catalog paths without network access.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH_FIELDS = (
    "specs", "workflows", "entrypoints", "code", "tests", "documentation",
)
INLINE_LINK = re.compile(r"\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)")
REFERENCE_LINK = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)", re.M)


def markdown_files(root: Path) -> list[Path]:
    """Select public documentation; agent instructions are a separate surface."""
    files = set(root.glob("*.md"))
    for folder in ("docs", "specs", "experiments", "cli"):
        files.update((root / folder).rglob("*.md"))
    return sorted(files)


def without_code(source: str) -> str:
    """Ignore fenced and inline examples while preserving diagnostic lines."""
    lines = []
    fence: str | None = None
    length = 0
    for line in source.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence is None and marker:
            fence, length = marker[1][0], len(marker[1])
            lines.append("\n" if line.endswith("\n") else "")
        elif fence is not None:
            if (
                marker and marker[1][0] == fence
                and len(marker[1]) >= length and not marker[2].strip()
            ):
                fence = None
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(re.sub(r"(`+).*?\1", "", line))
    return "".join(lines)


def missing_target(root: Path, base: Path, target: str) -> bool:
    """Check local files only; fragments/queries and external URLs are ignored."""
    parsed = urlsplit(target.strip("<>"))
    if parsed.scheme or parsed.netloc or not parsed.path:
        return False
    destination = (base / unquote(parsed.path)).resolve()
    return not destination.is_relative_to(root.resolve()) or not destination.exists()


def check_markdown_links(root: Path) -> list[str]:
    """Return file-link errors; HTML, anchors and remote URLs are not checked."""
    errors = []
    for path in markdown_files(root):
        source = without_code(path.read_text(encoding="utf-8"))
        for pattern in (INLINE_LINK, REFERENCE_LINK):
            for match in pattern.finditer(source):
                if missing_target(root, path.parent, match[1]):
                    line = source.count("\n", 0, match.start()) + 1
                    errors.append(
                        f"{path.relative_to(root)}:{line}: "
                        f"missing local file {match[1]}"
                    )
    return errors


def check_catalog(root: Path) -> list[str]:
    """Check inventory IDs and repository-relative file references."""
    path = root / "specs/catalog.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"specs/catalog.json: cannot read catalog ({type(error).__name__})"]
    if (
        not isinstance(catalog, dict) or catalog.get("version") != 1
        or not isinstance(catalog.get("capabilities"), list)
    ):
        return ["specs/catalog.json: expected version 1 capability inventory"]
    errors = []
    seen = set()
    for capability in catalog["capabilities"]:
        if not isinstance(capability, dict):
            errors.append("specs/catalog.json: capability must be an object")
            continue
        identifier = capability.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            errors.append("specs/catalog.json: invalid or duplicate capability ID")
        else:
            seen.add(identifier)
        for field in CATALOG_PATH_FIELDS:
            paths = capability.get(field)
            if not isinstance(paths, list) or not all(
                isinstance(p, str) for p in paths
            ):
                errors.append(
                    f"specs/catalog.json: {identifier}.{field} must list paths"
                )
                continue
            for target in paths:
                if missing_target(root, root, target):
                    errors.append(f"specs/catalog.json: {identifier}.{field}: {target}")
    return errors


def main() -> int:
    """Run the offline documentation gate."""
    errors = check_markdown_links(ROOT) + check_catalog(ROOT)
    if errors:
        print("DOCUMENTATION_CHECK_FAILED:\n" + "\n".join(errors))
        return 1
    print("DOCUMENTATION_CHECK_OK: local Markdown file links and SDD catalog paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

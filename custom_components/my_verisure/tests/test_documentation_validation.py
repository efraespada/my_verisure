"""Behavior contracts for the offline documentation gate.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json
from pathlib import Path

from scripts.check_documentation import (
    CATALOG_PATH_FIELDS, check_catalog, check_markdown_links,
)


def test_local_links_decode_paths_and_ignore_fragments_queries_and_urls(tmp_path):
    """Existence checking follows local links without making remote requests."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/space name.md").write_text("# Destination\n")
    (tmp_path / "README.md").write_text(
        "[file](docs/space%20name.md#missing-anchor)\n"
        "[query](docs/space%20name.md?raw=1)\n"
        "[remote](https://example.invalid/missing)\n"
        "[fragment](#unchecked-anchor)\n"
        "[ref][target]\n[target]: <docs/space name.md>\n"
    )
    assert check_markdown_links(tmp_path) == []


def test_missing_links_report_file_line_and_reference_destination(tmp_path):
    (tmp_path / "README.md").write_text(
        "# Example\n\n[broken](missing.md)\n[ref]: missing-reference.md\n"
    )
    errors = check_markdown_links(tmp_path)
    assert errors == [
        "README.md:3: missing local file missing.md",
        "README.md:4: missing local file missing-reference.md",
    ]


def test_code_examples_are_not_treated_as_project_links(tmp_path):
    (tmp_path / "README.md").write_text(
        "```md\n[broken](fenced.md)\n```\n"
        "~~~markdown\n[broken](tilde.md)\n~~~\n"
        "`[broken](inline.md)`\n[real](missing.md)\n"
    )
    assert check_markdown_links(tmp_path) == [
        "README.md:8: missing local file missing.md"
    ]


def test_links_cannot_escape_the_repository(tmp_path):
    (tmp_path / "README.md").write_text("[outside](../)\n")
    assert check_markdown_links(tmp_path) == [
        "README.md:1: missing local file ../"
    ]


def _catalog(root: Path, capability: dict) -> None:
    (root / "specs").mkdir(exist_ok=True)
    (root / "specs/catalog.json").write_text(
        json.dumps({"version": 1, "capabilities": [capability]})
    )


def test_catalog_checks_every_source_test_workflow_and_documentation_path(tmp_path):
    (tmp_path / "present.py").write_text("# synthetic\n")
    capability = {"id": "synthetic"}
    capability.update({key: ["present.py"] for key in CATALOG_PATH_FIELDS})
    _catalog(tmp_path, capability)
    assert check_catalog(tmp_path) == []
    capability["tests"] = ["missing-test.py"]
    _catalog(tmp_path, capability)
    assert check_catalog(tmp_path) == [
        "specs/catalog.json: synthetic.tests: missing-test.py"
    ]


def test_catalog_rejects_duplicate_ids_and_invalid_shapes(tmp_path):
    capability = {"id": "synthetic"}
    capability.update({key: [] for key in CATALOG_PATH_FIELDS})
    _catalog(tmp_path, capability)
    path = tmp_path / "specs/catalog.json"
    path.write_text(json.dumps({"version": 1, "capabilities": [capability] * 2}))
    assert "duplicate" in check_catalog(tmp_path)[0]
    path.write_text("not json")
    assert "cannot read catalog" in check_catalog(tmp_path)[0]

"""Tests for the installable integration artifact validation."""

from pathlib import Path

import pytest

from scripts.validate_distribution import validate_tree


def test_validate_tree_accepts_current_repository() -> None:
    validate_tree()


def test_validate_tree_rejects_tracked_generated_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import validate_distribution

    generated = Path(".coverage")
    monkeypatch.setattr(
        validate_distribution,
        "tracked_files",
        lambda: [validate_distribution.ROOT / generated],
    )

    with pytest.raises(ValueError, match="Generated artifacts"):
        validate_tree()

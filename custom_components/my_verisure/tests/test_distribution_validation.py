"""Tests for the installable integration artifact validation."""

from pathlib import Path

import pytest

from scripts.validate_distribution import validate_tree


def test_package_contains_event_runtime_and_excludes_tests(tmp_path, monkeypatch):
    from zipfile import ZipFile
    from scripts import validate_distribution as distribution

    integration = tmp_path / "custom_components" / "my_verisure"
    names = distribution.REQUIRED | {"core/tests/unit/test_synthetic.py", "tests/conftest.py"}
    files = []
    for name in names:
        path = integration / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic distribution fixture\n")
        files.append(path)
    monkeypatch.setattr(distribution, "ROOT", tmp_path)
    monkeypatch.setattr(distribution, "INTEGRATION", integration)
    monkeypatch.setattr(distribution, "tracked_files", lambda: files)
    artifact = distribution.create_and_validate_zip()
    with ZipFile(artifact) as archive:
        paths = archive.namelist()
        assert "custom_components/my_verisure/event.py" in paths
        assert "custom_components/my_verisure/notification_runtime.py" in paths
        assert all("tests" not in path.split("/") for path in paths)


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

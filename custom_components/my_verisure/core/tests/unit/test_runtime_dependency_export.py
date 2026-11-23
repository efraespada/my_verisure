"""Dependency audits cover a closed graph and expose only public versions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from types import SimpleNamespace

import pytest

from scripts import export_runtime_requirements as exporter


def test_export_deduplicates_cycles_and_skips_inactive_optional_dependencies(
    monkeypatch,
):
    packages = {
        "Package-A": SimpleNamespace(
            version="1.0",
            requires=[
                "b>=1",
                "docs-only; extra == 'docs'",
                "old-only; python_version < '2'",
            ],
        ),
        "b": SimpleNamespace(version="2.0", requires=["Package-A"]),
    }
    looked_up = []

    def distribution(name):
        looked_up.append(name)
        return packages[name]

    monkeypatch.setattr(exporter, "distribution", distribution)

    assert exporter.runtime_requirements(["Package-A"]) == ["b==2.0", "package-a==1.0"]
    assert looked_up == ["Package-A", "b"]


def test_extras_fail_explicitly_instead_of_silently_underreporting():
    with pytest.raises(ValueError, match="extras"):
        exporter.runtime_requirements(["package[extra]"])

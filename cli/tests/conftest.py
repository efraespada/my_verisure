"""Keep CLI tests away from the operator's actual persisted account.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import pytest

from custom_components.my_verisure.core.dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)


@pytest.fixture(autouse=True)
def isolated_cli_state(tmp_path, monkeypatch):
    def build_root():
        return build_my_verisure_composition_root(project_root=tmp_path / "cli-state")

    monkeypatch.setattr("cli.commands.base.build_cli_composition_root", build_root)

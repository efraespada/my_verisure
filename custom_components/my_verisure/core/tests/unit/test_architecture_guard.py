"""Exercise architecture rules against real Python import syntax.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from pathlib import Path

import pytest

from scripts.architecture_guard import check_imports


@pytest.mark.parametrize(
    ("relative_path", "source"),
    [
        ("core/application/new_policy.py", "from ..file_manager import FileManager"),
        ("core/application/models/new_model.py", "from ...api import auth_client"),
        ("core/use_cases/implementations/new_case.py", "from ... import api"),
        ("core/repositories/interfaces/new_port.py", "import aiohttp as transport"),
        ("core/application/new_policy.py", "import homeassistant.core as ha"),
        ("core/new_adapter.py", "from homeassistant import core"),
        ("core/application/new_policy.py", "from injector import Injector"),
        ("core/use_cases/implementations/new_case.py", "from PIL import Image"),
        (
            "core/application/models/new_model.py",
            "from ..notifications import NotificationHub",
        ),
    ],
)
def test_guard_rejects_outward_imports(tmp_path, relative_path, source):
    module = tmp_path / "custom_components/my_verisure" / relative_path
    module.parent.mkdir(parents=True)
    module.write_text(source, encoding="utf-8")

    errors = check_imports(tmp_path)

    assert len(errors) == 1
    assert relative_path in errors[0]


def test_guard_accepts_inward_imports_and_does_not_parse_comments(tmp_path):
    sources = {
        "core/application/policy.py": (
            "# api. and homeassistant are documentation here\n"
            "from .models.alarm import AlarmStatus\n"
        ),
        "core/api/client.py": "from ..application.models.alarm import AlarmStatus",
        "core/use_cases/implementations/case.py": (
            "from ...repositories.interfaces.alarm_repository import AlarmRepository"
        ),
        "core/application/models/new_model.py": "from .alarm import AlarmStatus",
    }
    for relative_path, source in sources.items():
        module = tmp_path / "custom_components/my_verisure" / relative_path
        module.parent.mkdir(parents=True, exist_ok=True)
        module.write_text(source, encoding="utf-8")

    assert check_imports(tmp_path) == []


def test_repository_core_has_no_outward_policy_imports():
    root = Path(__file__).resolve().parents[5]

    assert check_imports(root) == []

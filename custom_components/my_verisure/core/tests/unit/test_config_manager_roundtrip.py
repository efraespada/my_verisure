"""Exercise persisted configuration through its public interface.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from custom_components.my_verisure.core.config_manager import ConfigManager
from custom_components.my_verisure.core.file_manager import FileManager


def test_saved_settings_survive_reopening(tmp_path):
    files = FileManager(tmp_path)
    config = ConfigManager(files)
    assert config.set_setting("debug", True)
    assert config.set_setting("timeout", 75)

    reopened = ConfigManager(files)
    assert reopened.get_setting("debug") is True
    assert reopened.get_setting("timeout") == 75
    assert "metadata" not in reopened.get_config()
    assert "config" not in reopened.get_config()


def test_default_nested_settings_are_not_shared_with_callers(tmp_path):
    config = ConfigManager(FileManager(tmp_path))
    first = config.get_config()
    first["features"]["alarm"] = False
    first["notifications"]["enabled"] = False

    assert config.get_config()["features"]["alarm"] is True
    assert config.get_config()["notifications"]["enabled"] is True


def test_envelope_and_legacy_plain_configuration_are_readable(tmp_path):
    files = FileManager(tmp_path)
    config = ConfigManager(files)
    assert files.save_json("my_verisure_config.json", {"debug": True})
    assert config.get_setting("debug") is True
    assert config.save_config({"debug": True, "features": {"cameras": True}})
    assert config.get_setting("debug") is True
    assert config.get_config()["features"]["cameras"] is True

"""Tests for entry-scoped log and configuration managers."""

from pathlib import Path

from custom_components.my_verisure.core.config_manager import ConfigManager
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.log_manager import LogManager


def test_managers_prefer_injected_file_manager(tmp_path: Path):
    file_manager = FileManager(tmp_path)

    log_manager = LogManager(file_manager=file_manager)
    config_manager = ConfigManager(file_manager=file_manager)

    assert log_manager._resolve_file_manager() is file_manager
    assert config_manager._resolve_file_manager() is file_manager

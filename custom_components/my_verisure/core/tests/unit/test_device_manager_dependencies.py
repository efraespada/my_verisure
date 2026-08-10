"""Tests for entry-scoped file ownership in DeviceManager."""

from pathlib import Path

from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.file_manager import FileManager


def test_device_manager_prefers_injected_file_manager(tmp_path: Path):
    file_manager = FileManager(tmp_path)

    manager = DeviceManager(file_manager=file_manager)

    assert manager._resolve_file_manager() is file_manager

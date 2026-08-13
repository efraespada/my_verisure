"""Tests for entry-scoped file ownership in DeviceManager."""

from pathlib import Path
from unittest.mock import patch

from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.file_manager import FileManager


def test_device_manager_prefers_injected_file_manager(tmp_path: Path):
    file_manager = FileManager(tmp_path)

    manager = DeviceManager(file_manager=file_manager)

    assert manager._resolve_file_manager() is file_manager


def test_device_manager_platform_cache_is_instance_scoped(tmp_path: Path):
    first = DeviceManager(file_manager=FileManager(tmp_path / "first"))
    second = DeviceManager(file_manager=FileManager(tmp_path / "second"))

    with patch(
        "custom_components.my_verisure.core.api.device_manager.platform.platform",
        side_effect=["first-platform", "second-platform"],
    ) as platform_info:
        assert first._platform_string_for_identifiers() == "first-platform"
        assert first._platform_string_for_identifiers() == "first-platform"
        assert second._platform_string_for_identifiers() == "second-platform"

    assert platform_info.call_count == 2
    assert first._platform_string != second._platform_string

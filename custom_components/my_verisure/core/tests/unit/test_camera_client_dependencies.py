"""Tests for entry-scoped file ownership in CameraClient."""

from pathlib import Path
from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.file_manager import FileManager


def test_camera_client_prefers_injected_file_manager(tmp_path: Path):
    file_manager = FileManager(tmp_path)

    client = CameraClient(file_manager=file_manager)

    assert client._resolve_file_manager() is file_manager

"""Tests for entry-scoped installation cache ownership."""

from pathlib import Path

from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.repositories.implementations.installation_repository_impl import (
    InstallationRepositoryImpl,
)


def test_installation_repository_prefers_injected_file_manager(tmp_path: Path):
    file_manager = FileManager(tmp_path)

    repository = InstallationRepositoryImpl(client=object(), file_manager=file_manager)

    assert repository._file_manager is file_manager

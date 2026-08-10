"""Session manager file ownership tests."""

from pathlib import Path

from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def test_session_manager_accepts_entry_scoped_file_manager(tmp_path: Path):
    file_manager = FileManager(tmp_path)

    manager = SessionManager(tmp_path / "session.json", file_manager=file_manager)

    assert manager.file_manager is file_manager

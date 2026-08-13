"""Tests for entry-scoped dependency module construction."""

import pytest

from custom_components.my_verisure.core.dependency_injection.module import MyVerisureModule
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


def test_module_requires_explicit_entry_scoped_managers():
    with pytest.raises(TypeError):
        MyVerisureModule()  # type: ignore[call-arg]


def test_module_returns_the_supplied_managers(tmp_path):
    file_manager = FileManager(tmp_path)
    session_manager = SessionManager(
        tmp_path / "session.json", file_manager=file_manager
    )
    module = MyVerisureModule(
        session_manager=session_manager,
        file_manager=file_manager,
    )

    assert module.provide_file_manager() is file_manager
    assert module.provide_session_manager() is session_manager

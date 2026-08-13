"""Tests for concurrent entry isolation."""

import asyncio
import json
from pathlib import Path

import pytest

from custom_components.my_verisure.core.config_manager import ConfigManager
from custom_components.my_verisure.core.dependency_injection.composition_root import (
    build_my_verisure_composition_root,
)
from custom_components.my_verisure.core.log_manager import LogManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.asyncio
async def test_concurrent_entries_keep_sessions_and_files_isolated(tmp_path: Path) -> None:
    first_root = build_my_verisure_composition_root(
        session_file=tmp_path / "first" / "session.json",
        project_root=tmp_path / "first",
    )
    second_root = build_my_verisure_composition_root(
        session_file=tmp_path / "second" / "session.json",
        project_root=tmp_path / "second",
    )

    first_session = first_root.get(SessionManager)
    second_session = second_root.get(SessionManager)
    first_session.username = "entry-first"
    first_session.password = "[REDACTED]"
    first_session.hash_token = "first-token"
    first_session.session_timestamp = 1.0
    second_session.username = "entry-second"
    second_session.password = "[REDACTED]"
    second_session.hash_token = "second-token"
    second_session.session_timestamp = 2.0

    first_config = first_root.get(ConfigManager)
    second_config = second_root.get(ConfigManager)
    first_logs = first_root.get(LogManager)
    second_logs = second_root.get(LogManager)

    await asyncio.gather(
        first_session.async_persist_session_to_disk(),
        second_session.async_persist_session_to_disk(),
        asyncio.to_thread(first_config.save_config, {"marker": "first"}),
        asyncio.to_thread(second_config.save_config, {"marker": "second"}),
        asyncio.to_thread(first_logs.log_event, "test", "first-entry"),
        asyncio.to_thread(second_logs.log_event, "test", "second-entry"),
    )

    first_session_data = json.loads(first_session.session_file and Path(first_session.session_file).read_text())
    second_session_data = json.loads(second_session.session_file and Path(second_session.session_file).read_text())
    assert first_session_data["username"] == "entry-first"
    assert second_session_data["username"] == "entry-second"
    assert first_session_data["hash_token"] == "first-token"
    assert second_session_data["hash_token"] == "second-token"

    first_config_data = json.loads(
        (tmp_path / "first" / "data" / "my_verisure_config.json").read_text()
    )
    second_config_data = json.loads(
        (tmp_path / "second" / "data" / "my_verisure_config.json").read_text()
    )
    assert first_config_data["config"]["marker"] == "first"
    assert second_config_data["config"]["marker"] == "second"

    assert first_logs.get_logs()[0]["message"] == "first-entry"
    assert second_logs.get_logs()[0]["message"] == "second-entry"

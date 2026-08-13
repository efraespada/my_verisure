"""Tests for the coordinator snapshot persistence boundary."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.coordinator_snapshot_store import (
    CoordinatorSnapshotStore,
)


def test_load_returns_only_non_empty_mapping():
    file_manager = Mock()
    file_manager.load_json.return_value = {"alarm_status": {"status": "armed"}}
    store = CoordinatorSnapshotStore(file_manager)

    assert store.load() == {"alarm_status": {"status": "armed"}}
    file_manager.load_json.assert_called_once_with("coordinator_data.json")


def test_load_rejects_empty_and_non_mapping_payloads():
    file_manager = Mock()
    store = CoordinatorSnapshotStore(file_manager)

    for payload in ({}, [], None, "invalid"):
        file_manager.load_json.return_value = payload
        assert store.load() == {}


@pytest.mark.asyncio
async def test_save_delegates_to_async_file_manager():
    file_manager = Mock()
    file_manager.async_save_json = AsyncMock(return_value=True)
    store = CoordinatorSnapshotStore(file_manager)
    payload = {"installation_id": "home-1"}

    assert await store.save(payload) is True
    file_manager.async_save_json.assert_awaited_once_with(
        "coordinator_data.json", payload
    )


def test_metadata_uses_file_manager_information(tmp_path: Path):
    snapshot_path = tmp_path / "coordinator_data.json"
    snapshot_path.touch()
    file_manager = Mock()
    file_manager.get_file_path.return_value = snapshot_path
    file_manager.get_file_size.return_value = 42
    file_manager.file_exists.return_value = True
    store = CoordinatorSnapshotStore(file_manager)

    result = store.metadata()

    assert result["file_path"].endswith("coordinator_data.json")
    assert result["file_size"] == 42
    assert result["exists"] is True
    assert "last_modified" in result

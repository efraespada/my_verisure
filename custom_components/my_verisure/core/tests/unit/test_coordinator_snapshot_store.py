"""Tests for the coordinator snapshot persistence boundary."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.coordinator_snapshot_store import (
    CoordinatorSnapshotStore,
)


def test_load_returns_a_sanitized_non_empty_mapping():
    file_manager = Mock()
    file_manager.load_json.return_value = {
        "installation_id": "INSTALLATION_SENTINEL",
        "alarm_status": {"data": {"internal": {"total": {"status": True}}}},
        "detailed_installation": {
            "installation": {
                "alias": "PRIVATE_ALIAS",
                "panel": "PRIVATE_PANEL",
                "capabilities": "PRIVATE_CAPABILITIES",
            }
        },
    }
    store = CoordinatorSnapshotStore(file_manager)

    result = store.load()

    serialized = str(result)
    assert "INSTALLATION_SENTINEL" not in serialized
    assert "PRIVATE_ALIAS" not in serialized
    assert "PRIVATE_PANEL" not in serialized
    assert "PRIVATE_CAPABILITIES" not in serialized
    assert result["alarm_status"]["data"]["internal"]["total"]["status"] is True




def test_load_rejects_malformed_legacy_alarm_envelope():
    file_manager = Mock()
    file_manager.load_json.return_value = {
        "alarm_status": {"data": []},
        "detailed_installation": {"installation": {"status": "PRIVATE_STATUS"}},
    }

    assert CoordinatorSnapshotStore(file_manager).load() == {}


def test_snapshot_projection_omits_provider_status_and_role():
    file_manager = Mock()
    file_manager.load_json.return_value = {
        "alarm_status": {"data": {}},
        "detailed_installation": {
            "installation": {"status": "PRIVATE_STATUS", "role": "PRIVATE_ROLE"}
        },
    }

    result = CoordinatorSnapshotStore(file_manager).load()

    assert "status" not in result["detailed_installation"]["installation"]
    assert "role" not in result["detailed_installation"]["installation"]


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
    payload = {
        "installation_id": "INSTALLATION_SENTINEL",
        "alarm_status": {
            "data": {
                "internal": {"total": {"status": True}},
                "external": {"status": False},
            }
        },
        "detailed_installation": {
            "installation": {
                "status": "active",
                "role": "owner",
                "alias": "PRIVATE_ALIAS",
                "panel": "PRIVATE_PANEL",
                "capabilities": "PRIVATE_CAPABILITIES",
                "devices": [{"name": "PRIVATE_DEVICE", "code": "PRIVATE_CODE"}],
                "services": [{"idService": "PRIVATE_SERVICE", "active": True, "visible": False}],
            }
        },
    }

    assert await store.save(payload) is True
    saved_payload = file_manager.async_save_json.await_args.args[1]
    serialized = str(saved_payload)
    assert "INSTALLATION_SENTINEL" not in serialized
    assert "PRIVATE_ALIAS" not in serialized
    assert "PRIVATE_PANEL" not in serialized
    assert "PRIVATE_CAPABILITIES" not in serialized
    assert "PRIVATE_DEVICE" not in serialized
    assert "PRIVATE_CODE" not in serialized
    assert "PRIVATE_SERVICE" not in serialized
    assert saved_payload["alarm_status"]["data"]["internal"]["total"]["status"] is True


def test_metadata_uses_file_manager_information(tmp_path: Path):
    snapshot_path = tmp_path / "coordinator_data.json"
    snapshot_path.touch()
    file_manager = Mock()
    file_manager.get_file_path.return_value = snapshot_path
    file_manager.get_file_size.return_value = 42
    file_manager.file_exists.return_value = True
    store = CoordinatorSnapshotStore(file_manager)

    result = store.metadata()

    assert "file_path" not in result
    assert result["file_size"] == 42
    assert result["exists"] is True
    assert "last_modified" in result

"""Home Assistant platform contract tests for My Verisure."""

from pathlib import Path
from typing import cast
from types import SimpleNamespace


import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure import alarm_control_panel, binary_sensor, button, camera, sensor
from custom_components.my_verisure.camera import VerisureCamera, camera_unique_id
from custom_components.my_verisure.coordinator import MyVerisureDataUpdateCoordinator
from custom_components.my_verisure.core.const import DOMAIN


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="platform-entry",
        title="Platform test",
        data={"installation_id": "123", "user": "[REDACTED]", "password": "[REDACTED]"},
    )


def _coordinator(data: dict) -> SimpleNamespace:
    return SimpleNamespace(
        data=data,
        last_update_success=True,
        async_add_listener=lambda callback: lambda: None,
        register_button=lambda entity: None,
    )


def _camera_entity(tmp_path: Path, entry: MockConfigEntry) -> VerisureCamera:
    coordinator = _coordinator({})
    coordinator.file_manager = SimpleNamespace(get_data_directory=lambda: tmp_path)
    return VerisureCamera(
        cast(MyVerisureDataUpdateCoordinator, coordinator),
        {"type": "YP", "code": "1", "name": "Front"},
        entry,
    )


def test_camera_image_returns_none_when_directory_is_missing(tmp_path):
    entity = _camera_entity(tmp_path, _entry())

    assert entity._get_latest_image() is None


def test_camera_display_name_distinguishes_the_provider_camera(tmp_path):
    entity = _camera_entity(tmp_path, _entry())
    assert entity.name == "Verisure Front"


def test_camera_exposes_authenticated_proxy_after_initialization(tmp_path):
    """Exercise the camera properties read by HA while adding the entity."""
    entity = _camera_entity(tmp_path, _entry())
    entity.entity_id = "camera.test_verisure"

    assert entity.entity_picture.startswith("/api/camera_proxy/camera.test_verisure?token=")
    assert entity.state_attributes["access_token"]


def test_camera_image_ignores_invalid_timestamp_directories(tmp_path):
    entity = _camera_entity(tmp_path, _entry())
    device_path = tmp_path / "cameras" / "YP01"
    (device_path / "not-a-timestamp").mkdir(parents=True)

    assert entity._get_latest_image() is None


def test_camera_image_prefers_thumbnail(tmp_path):
    entity = _camera_entity(tmp_path, _entry())
    timestamp_path = tmp_path / "cameras" / "YP01" / "2026-08-13_12-00-00"
    timestamp_path.mkdir(parents=True)
    (timestamp_path / ".complete").write_bytes(b"complete")
    (timestamp_path / "thumbnail.jpg").write_bytes(b"thumbnail")
    (timestamp_path / "other.png").write_bytes(b"other")

    assert entity._get_latest_image() == b"thumbnail"
    assert entity._latest_image_path is not None
    assert entity._latest_image_path.endswith("thumbnail.jpg")


def test_camera_image_falls_back_to_supported_image(tmp_path):
    entity = _camera_entity(tmp_path, _entry())
    timestamp_path = tmp_path / "cameras" / "YP01" / "2026-08-13_12-00-00"
    timestamp_path.mkdir(parents=True)
    (timestamp_path / ".complete").write_bytes(b"complete")
    (timestamp_path / "snapshot.png").write_bytes(b"snapshot")

    assert entity._get_latest_image() == b"snapshot"


def test_camera_image_hides_uncommitted_directory(tmp_path):
    entity = _camera_entity(tmp_path, _entry())
    timestamp_path = tmp_path / "cameras" / "YP01" / "2026-08-13_12-00-00"
    timestamp_path.mkdir(parents=True)
    (timestamp_path / "thumbnail.jpg").write_bytes(b"partial")

    assert entity._get_latest_image() is None


def test_camera_image_hides_directory_with_partial_commit_marker(tmp_path):
    entity = _camera_entity(tmp_path, _entry())
    timestamp_path = tmp_path / "cameras" / "YP01" / "2026-08-13_12-00-00"
    timestamp_path.mkdir(parents=True)
    (timestamp_path / ".complete").write_bytes(b"incomplete")
    (timestamp_path / "thumbnail.jpg").write_bytes(b"partial")

    assert entity._get_latest_image() is None

@pytest.mark.asyncio
async def test_sensor_platform_creates_four_entry_scoped_entities():
    entry = _entry()
    entry.runtime_data = _coordinator({"alarm_status": {"data": {}}})
    added = []

    await sensor.async_setup_entry(None, entry, added.extend)

    assert len(added) == 4
    assert {entity.unique_id for entity in added} == {
        "platform-entry_alarm_status",
        "platform-entry_active_alarms",
        "platform-entry_panel_state",
        "platform-entry_last_updated",
    }
    assert all(entity.device_info["identifiers"] == {(DOMAIN, entry.entry_id)} for entity in added)


@pytest.mark.asyncio
async def test_active_alarm_sensor_hides_attributes_for_incomplete_alarm_data():
    entry = _entry()
    entry.runtime_data = _coordinator({"alarm_status": {"data": {}}})
    added = []

    await sensor.async_setup_entry(None, entry, added.extend)

    active_sensor = next(entity for entity in added if entity.sensor_id == "active_alarms")
    assert active_sensor.native_value is None
    assert active_sensor.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_binary_sensor_platform_creates_safety_entities():
    entry = _entry()
    entry.runtime_data = _coordinator({"alarm_status": {"data": {}}})
    added = []

    await binary_sensor.async_setup_entry(None, entry, added.extend)

    assert len(added) == 4
    assert {entity.unique_id for entity in added} == {
        "platform-entry_alarm_internal_day",
        "platform-entry_alarm_internal_night",
        "platform-entry_alarm_internal_total",
        "platform-entry_alarm_external",
    }
    assert all(entity.device_class.value == "safety" for entity in added)




@pytest.mark.asyncio
async def test_binary_sensor_reports_active_alarm_as_on():
    entry = _entry()
    entry.runtime_data = _coordinator(
        {
            "alarm_status": {
                "data": {
                    "internal": {
                        "day": {"status": True},
                        "night": {"status": False},
                        "total": {"status": False},
                    },
                    "external": {"status": False},
                }
            }
        }
    )
    added = []

    await binary_sensor.async_setup_entry(None, entry, added.extend)

    day_sensor = next(entity for entity in added if entity.sensor_id == "internal_day")
    assert day_sensor.is_on is True


@pytest.mark.asyncio
async def test_alarm_control_panel_exposes_expected_features_and_identity():
    entry = _entry()
    entry.runtime_data = _coordinator({"alarm_status": {"data": {}}})
    added = []

    await alarm_control_panel.async_setup_entry(None, entry, added.extend)

    assert len(added) == 1
    entity = added[0]
    assert entity.unique_id == "my_verisure-platform-entry"
    assert entity.code_format is None
    assert entity.code_arm_required is False
    assert entity._attr_code_disarm_required is False
    assert entity.supported_features


@pytest.mark.asyncio
async def test_alarm_control_panel_hides_attributes_for_unknown_alarm_data():
    entry = _entry()
    entry.runtime_data = _coordinator({"alarm_status": {"data": {}}})
    added = []

    await alarm_control_panel.async_setup_entry(None, entry, added.extend)

    entity = added[0]
    assert entity.alarm_state is None
    assert entity.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_alarm_control_panel_hides_attributes_for_partial_alarm_data():
    entry = _entry()
    entry.runtime_data = _coordinator(
        {"alarm_status": {"data": {"internal": {"total": {"status": True}}}}}
    )
    added = []

    await alarm_control_panel.async_setup_entry(None, entry, added.extend)

    entity = added[0]
    assert entity.alarm_state is None
    assert entity.extra_state_attributes == {}


@pytest.mark.asyncio
async def test_button_platform_creates_refresh_entity_from_installation_data():
    entry = _entry()
    entry.runtime_data = _coordinator({"installation_id": "123"})
    added = []
    options = []
    def add_entities(entities, **kwargs):
        added.extend(entities)
        options.append(kwargs)

    await button.async_setup_entry(None, entry, add_entities)

    assert len(added) == 1
    assert added[0].unique_id == "platform-entry_refresh_camera_images"
    assert "installation_id" not in added[0].extra_state_attributes
    assert options == [{}]


@pytest.mark.asyncio
async def test_camera_platform_creates_only_camera_devices():
    entry = _entry()
    entry.runtime_data = _coordinator(
        {
            "detailed_installation": {
                "installation": {
                    "devices": [
                        {"type": "YP", "code": "1", "name": "Front"},
                        {"type": "YR", "code": "2", "name": "Back"},
                        {"type": "SD", "code": "3", "name": "Sensor"},
                    ]
                }
            }
        }
    )
    added = []
    options = []
    def add_entities(entities, **kwargs):
        added.extend(entities)
        options.append(kwargs)

    await camera.async_setup_entry(None, entry, add_entities)

    assert {entity.unique_id for entity in added} == {
        camera_unique_id(entry.entry_id, {"type": "YP", "code": "1"}),
        camera_unique_id(entry.entry_id, {"type": "YR", "code": "2"}),
    }
    assert all(entity.content_type == "image/jpeg" for entity in added)
    assert options == [{}]


def test_camera_identity_is_stable_when_provider_reorders_devices(tmp_path):
    entry = _entry()
    coordinator = cast(MyVerisureDataUpdateCoordinator, _coordinator({}))
    front = {"type": "YP", "code": "1", "name": "Front"}
    back = {"type": "YR", "code": "2", "name": "Back"}

    first_front = VerisureCamera(coordinator, front, entry, 0)
    first_back = VerisureCamera(coordinator, back, entry, 1)
    reordered_front = VerisureCamera(coordinator, front, entry, 1)
    reordered_back = VerisureCamera(coordinator, back, entry, 0)

    assert first_front.unique_id == reordered_front.unique_id
    assert first_back.unique_id == reordered_back.unique_id
    assert first_front.unique_id != first_back.unique_id

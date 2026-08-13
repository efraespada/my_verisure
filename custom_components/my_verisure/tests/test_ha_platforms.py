"""Home Assistant platform contract tests for My Verisure."""

from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure import alarm_control_panel, binary_sensor, button, camera, sensor
from custom_components.my_verisure.core.const import DOMAIN


def _entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id="platform-entry",
        title="Platform test",
        data={"installation_id": "123", "user": "test@example.invalid", "password": "[REDACTED]"},
    )


def _coordinator(data: dict) -> SimpleNamespace:
    return SimpleNamespace(
        data=data,
        last_update_success=True,
        async_add_listener=lambda callback: lambda: None,
        register_button=lambda entity: None,
    )


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
    assert all(entity.device_info["identifiers"] == {(DOMAIN, "123")} for entity in added)


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
async def test_alarm_control_panel_exposes_expected_features_and_identity():
    entry = _entry()
    entry.runtime_data = _coordinator({"alarm_status": {"data": {}}})
    added = []

    await alarm_control_panel.async_setup_entry(None, entry, added.extend)

    assert len(added) == 1
    entity = added[0]
    assert entity.unique_id == "my_verisure"
    assert entity.code_format is None
    assert entity.code_arm_required is False
    assert entity._attr_code_disarm_required is False
    assert entity.supported_features


@pytest.mark.asyncio
async def test_button_platform_creates_refresh_entity_from_installation_data():
    entry = _entry()
    entry.runtime_data = _coordinator({"installation_id": "123"})
    added = []
    def add_entities(entities, **kwargs):
        added.extend(entities)

    await button.async_setup_entry(None, entry, add_entities)

    assert len(added) == 1
    assert added[0].unique_id == "platform-entry_refresh_camera_images"
    assert added[0].extra_state_attributes["installation_id"] == "123"


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
    def add_entities(entities, **kwargs):
        added.extend(entities)

    await camera.async_setup_entry(None, entry, add_entities)

    assert {entity.unique_id for entity in added} == {
        "platform-entry_camera_1",
        "platform-entry_camera_2",
    }
    assert all(entity.content_type == "image/jpeg" for entity in added)

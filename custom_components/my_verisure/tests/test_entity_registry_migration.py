"""Verify upgrades preserve real HA registry identities and customization.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from homeassistant.helpers import area_registry as ar, device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.my_verisure.camera import camera_unique_id
from custom_components.my_verisure.device import async_setup_device
from custom_components.my_verisure.entity_registry_migration import async_migrate_camera_entities


async def test_upgrade_keeps_original_device_alarm_and_area(hass):
    entry = MockConfigEntry(domain="my_verisure", data={"installation_id": "home"})
    entry.add_to_hass(hass)
    devices = dr.async_get(hass)
    entities = er.async_get(hass)
    old = devices.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("my_verisure", "home")}, name="Old")
    area = ar.async_get(hass).async_create("Entry")
    devices.async_update_device(old.id, area_id=area.id)
    new = devices.async_get_or_create(config_entry_id=entry.entry_id, identifiers={("my_verisure", entry.entry_id)}, name="New")
    old_alarm = entities.async_get_or_create("alarm_control_panel", "my_verisure", "my_verisure", config_entry=entry, device_id=old.id)
    entities.async_get_or_create("alarm_control_panel", "my_verisure", f"my_verisure-{entry.entry_id}", config_entry=entry, device_id=new.id)
    sensor = entities.async_get_or_create("sensor", "my_verisure", "sensor-key", config_entry=entry, device_id=new.id)

    await async_setup_device(hass, entry)

    assert devices.async_get_device(identifiers={("my_verisure", entry.entry_id)}).id == old.id
    assert devices.async_get(new.id) is None
    assert devices.async_get(old.id).area_id == area.id
    assert entities.async_get(sensor.entity_id).device_id == old.id
    assert entities.async_get_entity_id("alarm_control_panel", "my_verisure", f"my_verisure-{entry.entry_id}") == old_alarm.entity_id


async def test_camera_upgrade_matches_names_and_preserves_entity_id(hass):
    entry = MockConfigEntry(domain="my_verisure", data={})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    camera = {"type": "YP", "code": "17", "name": "Front porch"}
    legacy = registry.async_get_or_create("camera", "my_verisure", f"{entry.entry_id}_camera_17", config_entry=entry, suggested_object_id="alarm_verisure_front_porch", original_name="Verisure Camera")
    generic = registry.async_get_or_create("camera", "my_verisure", f"{entry.entry_id}_camera_0", config_entry=entry, suggested_object_id="my_verisure_alarm_verisure_camera", original_name="Verisure Camera")
    registry.async_update_entity(legacy.entity_id, name="My porch")
    key = camera_unique_id(entry.entry_id, camera)

    async_migrate_camera_entities(hass, entry, [(camera, key)])

    assert registry.async_get_entity_id("camera", "my_verisure", key) == legacy.entity_id
    assert registry.async_get(legacy.entity_id).name == "My porch"
    assert registry.async_get(generic.entity_id) is None


async def test_camera_upgrade_does_not_guess_unknown_camera_identity(hass):
    entry = MockConfigEntry(domain="my_verisure", data={})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = registry.async_get_or_create("camera", "my_verisure", f"{entry.entry_id}_camera_0", config_entry=entry, suggested_object_id="custom_camera", original_name="Verisure Camera")
    camera = {"type": "YP", "code": "17", "name": "Front porch"}

    async_migrate_camera_entities(hass, entry, [(camera, camera_unique_id(entry.entry_id, camera))])

    assert registry.async_get(old.entity_id).unique_id == old.unique_id


async def test_camera_upgrade_does_not_guess_duplicate_aliases(hass):
    entry = MockConfigEntry(domain="my_verisure", data={})
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    old = registry.async_get_or_create("camera", "my_verisure", f"{entry.entry_id}_camera_1", config_entry=entry, suggested_object_id="alarm_verisure_porch", original_name="Verisure Porch")
    cameras = [{"type": "YP", "code": code, "name": "Porch"} for code in ("1", "2")]

    async_migrate_camera_entities(hass, entry, [(camera, camera_unique_id(entry.entry_id, camera)) for camera in cameras])

    assert registry.async_get(old.entity_id).unique_id == old.unique_id


async def test_upgrade_does_not_claim_another_entries_device(hass):
    owner = MockConfigEntry(domain="my_verisure", data={"installation_id": "home"})
    other = MockConfigEntry(domain="my_verisure", data={"installation_id": "home"})
    owner.add_to_hass(hass)
    other.add_to_hass(hass)
    devices = dr.async_get(hass)
    old = devices.async_get_or_create(config_entry_id=owner.entry_id, identifiers={("my_verisure", "home")})

    await async_setup_device(hass, other)

    assert devices.async_get(old.id).identifiers == {("my_verisure", "home")}
    assert devices.async_get_device(identifiers={("my_verisure", other.entry_id)}).id != old.id

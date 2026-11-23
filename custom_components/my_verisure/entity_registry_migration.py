"""Preserve existing HA entity identities during identifier upgrades.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.util import slugify

from .core.const import DOMAIN


@callback
def async_migrate_camera_entities(
    hass: HomeAssistant, entry: ConfigEntry, cameras: list[tuple[dict, str]],
) -> None:
    """Match legacy cameras by their original generated name, never list position."""
    registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(registry, entry.entry_id)
    prefix = f"{entry.entry_id}_camera_"
    legacy = [entity for entity in entries if entity.domain == "camera" and entity.platform == DOMAIN and entity.unique_id.startswith(prefix)]
    matched = 0
    for device, unique_id in cameras:
        if registry.async_get_entity_id("camera", DOMAIN, unique_id):
            matched += 1
            continue
        name = device.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        if sum(other.get("name") == name for other, _ in cameras) != 1:
            continue
        suffix = slugify(f"Verisure {name}")
        candidates = [entity for entity in legacy if entity.entity_id.endswith(f"_{suffix}") or entity.original_name == f"Verisure {name}"]
        if len(candidates) == 1:
            registry.async_update_entity(candidates[0].entity_id, new_unique_id=unique_id)
            matched += 1

    # An interrupted index-based upgrade created extra generic entries. Only
    # retire these empty duplicates after every real camera was identified.
    if cameras and matched == len(cameras):
        desired = {unique_id for _, unique_id in cameras}
        for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
            if (
                entity.domain == "camera" and entity.platform == DOMAIN
                and entity.unique_id.startswith(prefix) and entity.unique_id not in desired
                and entity.original_name == "Verisure Camera"
                and entity.name is None and entity.icon is None
                and entity.area_id is None and not entity.labels
                and entity.entity_id.rsplit(".", 1)[-1].startswith("my_verisure_alarm_verisure_camera")
            ):
                registry.async_remove(entity.entity_id)


@callback
def async_migrate_alarm_entity(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Keep the original alarm entity ID used by dashboards and automations."""
    registry = er.async_get(hass)
    legacy_id = registry.async_get_entity_id("alarm_control_panel", DOMAIN, "my_verisure")
    legacy = registry.async_get(legacy_id) if legacy_id else None
    if legacy is None or legacy.config_entry_id != entry.entry_id:
        return
    unique_id = f"my_verisure-{entry.entry_id}"
    current_id = registry.async_get_entity_id("alarm_control_panel", DOMAIN, unique_id)
    if current_id:
        current = registry.async_get(current_id)
        if current is None or current.name is not None or current.icon is not None or current.area_id is not None or current.labels:
            return
        registry.async_remove(current_id)
    registry.async_update_entity(legacy.entity_id, new_unique_id=unique_id)

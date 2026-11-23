"""Safe notification diagnostics and independent entity lifecycle.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from datetime import datetime, timedelta, timezone
import json
import logging
from types import SimpleNamespace
from unittest.mock import Mock

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed_exact,
)

from custom_components.my_verisure import binary_sensor, sensor
from custom_components.my_verisure.core.const import DOMAIN
from custom_components.my_verisure.diagnostics import async_get_config_entry_diagnostics


class FakeHub:
    def __init__(self):
        self.listeners = []

    def subscribe_diagnostics(self, callback):
        self.listeners.append(callback)

        def unsubscribe():
            if callback in self.listeners:
                self.listeners.remove(callback)

        return unsubscribe

    def changed(self):
        for callback in tuple(self.listeners):
            callback()


def values():
    return {
        "enabled": True,
        "connected": False,
        "binding_state": "pending",
        "last_received": 1800000000.0,
        "last_accepted": 1800000001.0,
        "last_verified": 1800000002.0,
        "cooldown_remaining": 120.0,
        "counters": {"accepted": 2},
        "coverage": {"INF": 2},
    }


def context(data=None):
    data = values() if data is None else data
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id="diagnostic-entry",
        title="Synthetic home",
        data={"installation_id": "synthetic-home"},
    )
    owner = SimpleNamespace(
        notification_hub=FakeHub(),
        notification_diagnostics=lambda: dict(data),
        last_update_success=False,
        data={},
        update_interval=None,
        session_manager=SimpleNamespace(
            is_authenticated=False,
            is_session_valid=lambda: False,
        ),
    )
    config_entry.runtime_data = owner
    return config_entry, owner, data


@pytest.mark.parametrize("key", ["last_received", "last_accepted", "last_verified"])
@pytest.mark.parametrize(
    "value",
    [
        None,
        "synthetic-private-value",
        True,
        float("nan"),
        float("inf"),
        1e308,
        -1e308,
    ],
)
def test_timestamp_diagnostics_reject_invalid_values(key, value):
    config_entry, owner, data = context()
    data[key] = value
    entity = sensor.MyVerisureNotificationDiagnosticSensor(owner, config_entry, key)
    assert entity.native_value is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("last_received", datetime.fromtimestamp(1800000000.0, timezone.utc)),
        ("last_accepted", datetime.fromtimestamp(1800000001.0, timezone.utc)),
        ("last_verified", datetime.fromtimestamp(1800000002.0, timezone.utc)),
        ("binding_state", "pending"),
        ("cooldown_remaining", 120.0),
    ],
)
def test_diagnostic_entities_use_only_typed_summary_values(key, value):
    config_entry, owner, _data = context()
    entity = sensor.MyVerisureNotificationDiagnosticSensor(owner, config_entry, key)
    assert entity.native_value == value
    assert entity.entity_category is EntityCategory.DIAGNOSTIC
    assert not entity.entity_registry_enabled_default
    assert entity.unique_id == f"diagnostic-entry_push_{key}"
    assert entity.available
    assert not entity.should_poll


@pytest.mark.parametrize("value", [None, "secret", -1, True, float("nan")])
def test_cooldown_rejects_invalid_numbers(value):
    config_entry, owner, data = context()
    data["cooldown_remaining"] = value
    entity = sensor.MyVerisureNotificationDiagnosticSensor(
        owner,
        config_entry,
        "cooldown_remaining",
    )
    assert entity.native_value is None


@pytest.mark.parametrize("value", [None, "synthetic-private-value", {}])
def test_binding_state_does_not_expose_unknown_provider_text(value):
    config_entry, owner, data = context()
    data["binding_state"] = value
    entity = sensor.MyVerisureNotificationDiagnosticSensor(
        owner,
        config_entry,
        "binding_state",
    )
    assert entity.native_value is None


@pytest.mark.parametrize(
    "enabled,connected,expected",
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
        (True, None, None),
        (True, "private", None),
    ],
)
def test_connectivity_is_transport_only_and_independent_of_alarm_poll(
    enabled,
    connected,
    expected,
):
    config_entry, owner, data = context()
    data.update(enabled=enabled, connected=connected)
    entity = binary_sensor.MyVerisurePushConnectivitySensor(owner, config_entry)
    assert entity.is_on is expected
    assert entity.available
    assert entity.entity_registry_enabled_default
    assert entity.entity_category is EntityCategory.DIAGNOSTIC


@pytest.mark.homeassistant
async def test_diagnostic_platforms_attach_and_remove_entry_owned_callbacks(hass):
    config_entry, owner, data = context()
    config_entry.add_to_hass(hass)
    sensor_entities, binary_entities = [], []
    await sensor.async_setup_entry(hass, config_entry, sensor_entities.extend)
    await binary_sensor.async_setup_entry(hass, config_entry, binary_entities.extend)
    diagnostic_sensors = [
        item
        for item in sensor_entities
        if isinstance(item, sensor.MyVerisureNotificationDiagnosticSensor)
    ]
    connectivity = next(
        item
        for item in binary_entities
        if isinstance(item, binary_sensor.MyVerisurePushConnectivitySensor)
    )
    assert len(diagnostic_sensors) == 5
    component = EntityComponent(logging.getLogger(__name__), "sensor", hass)
    component._platforms["sensor"].config_entry = config_entry
    component.register_shutdown()
    for index, item in enumerate(diagnostic_sensors):
        item.entity_id = f"sensor.notification_diagnostic_{index}"
        item._attr_entity_registry_enabled_default = True
    await component.async_add_entities(diagnostic_sensors)
    binary_component = EntityComponent(
        logging.getLogger(__name__),
        "binary_sensor",
        hass,
    )
    binary_component._platforms["binary_sensor"].config_entry = config_entry
    binary_component.register_shutdown()
    connectivity.entity_id = "binary_sensor.notification_connected"
    await binary_component.async_add_entities([connectivity])
    await hass.async_block_till_done()
    assert len(owner.notification_hub.listeners) == 6
    data["connected"] = True
    owner.notification_hub.changed()
    await hass.async_block_till_done()
    assert hass.states.get(connectivity.entity_id).state == "on"
    for item in tuple(component.entities):
        await component.async_remove_entity(item.entity_id)
    await binary_component.async_remove_entity(connectivity.entity_id)
    assert owner.notification_hub.listeners == []


@pytest.mark.homeassistant
async def test_diagnostics_exports_only_safe_notification_summary(hass):
    config_entry, owner, data = context()
    result = await async_get_config_entry_diagnostics(hass, config_entry)
    assert result["coordinator"]["notifications"] == data
    assert "synthetic-private-value" not in json.dumps(result)


@pytest.mark.homeassistant
async def test_diagnostics_summary_failure_does_not_expose_exception(hass):
    config_entry, owner, _data = context()

    def fail():
        raise RuntimeError("synthetic-private-value")

    owner.notification_diagnostics = fail
    result = await async_get_config_entry_diagnostics(hass, config_entry)
    assert "synthetic-private-value" not in json.dumps(result)
    assert result["coordinator"]["notifications"]["error"] == (
        "Notification diagnostics unavailable"
    )


@pytest.mark.homeassistant
async def test_local_cooldown_heartbeat_detects_block_expires_and_stops(hass):
    config_entry, owner, data = context()
    config_entry.add_to_hass(hass)
    data["cooldown_remaining"] = 0.0
    reader = Mock(side_effect=lambda: dict(data))
    owner.notification_diagnostics = reader
    value = sensor.MyVerisureNotificationDiagnosticSensor(
        owner,
        config_entry,
        "cooldown_remaining",
    )
    value.entity_id = "sensor.notification_cooldown"
    value._attr_entity_registry_enabled_default = True
    component = EntityComponent(logging.getLogger(__name__), "sensor", hass)
    component._platforms["sensor"].config_entry = config_entry
    component.register_shutdown()
    await component.async_add_entities([value])
    await hass.async_block_till_done()
    assert hass.states.get(value.entity_id).state == "0.0"
    data["cooldown_remaining"] = 5.0
    async_fire_time_changed_exact(hass, dt_util.utcnow() + timedelta(seconds=31))
    await hass.async_block_till_done()
    assert hass.states.get(value.entity_id).state == "5.0"
    data["cooldown_remaining"] = 0.0
    async_fire_time_changed_exact(hass, dt_util.utcnow() + timedelta(seconds=6))
    await hass.async_block_till_done()
    assert hass.states.get(value.entity_id).state == "0.0"
    await component.async_remove_entity(value.entity_id)
    reads = reader.call_count
    # A callback already queued before removal must not resurrect the timer.
    value._cooldown_tick(dt_util.utcnow())
    async_fire_time_changed_exact(hass, dt_util.utcnow() + timedelta(seconds=180))
    await hass.async_block_till_done()
    assert reader.call_count == reads

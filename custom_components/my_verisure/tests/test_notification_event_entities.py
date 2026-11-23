"""Real HA event lifecycle, native triggers, restore and bus projection.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from datetime import datetime, timezone
import json
import logging
from types import SimpleNamespace
from unittest.mock import Mock

from homeassistant.components.event import EventExtraStoredData
from homeassistant.components.event.trigger import EventReceivedTrigger
from homeassistant.core import Context, State
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.trigger import TriggerConfig
import pytest
from pytest_homeassistant.common import (
    MockConfigEntry,
    mock_restore_cache_with_extra_data,
)

from custom_components.my_verisure import event as event_platform
from custom_components.my_verisure.core.const import DOMAIN


class FakeHub:
    def __init__(self):
        self.listeners = []
        self.active = False
        self.buffer = []

    def subscribe(self, callback):
        self.listeners.append(callback)

        def unsubscribe():
            if callback in self.listeners:
                self.listeners.remove(callback)

        return unsubscribe

    def activate(self):
        self.active = True
        self.buffer.clear()

    def emit(self, event):
        if not self.active:
            self.buffer.append(event)
            return
        for callback in tuple(self.listeners):
            callback(event)


class FakeEvent:
    def __init__(self, kind="photo_ready", stage="confirmed", event_id="event-one"):
        self.kind = kind
        self.stage = stage
        self.event_id = event_id
        self.raw_payload = {"token": "synthetic-private-value"}

    def public_data(self):
        return {
            "schema_version": 1,
            "event_id": self.event_id,
            "correlation_id": "local-correlation",
            "kind": self.kind,
            "stage": self.stage,
            "category": "photo",
            "scope": "installation",
            "provider_request": "INF",
            "received_at": "2026-11-23T02:00:00Z",
            "occurred_at": None,
            "verified_at": "2026-11-23T02:00:00Z",
            "freshness": "fresh",
            "delivery": "live",
            "verification": "authoritative_read",
            "subject_entity_id": None,
        }


def entry(options=None, identity="notification-entry"):
    return MockConfigEntry(
        domain=DOMAIN,
        entry_id=identity,
        title="Synthetic installation",
        data={"installation_id": "synthetic-home", "user": "synthetic-user"},
        options=options or {},
    )


def coordinator(hub):
    return SimpleNamespace(
        notification_hub=hub,
        last_update_success=False,
        notification_diagnostics=lambda: {"connected": False, "enabled": True},
    )


async def add_real_entity(hass, config_entry, hub, stage="confirmed"):
    if config_entry.entry_id not in hass.config_entries.async_entry_ids():
        config_entry.add_to_hass(hass)
    value = event_platform.MyVerisureNotificationEvent(
        coordinator(hub),
        config_entry,
        stage,
    )
    value.entity_id = f"event.{config_entry.entry_id.replace('-', '_')}_{stage}"
    component = EntityComponent(logging.getLogger(__name__), "event", hass)
    component._platforms["event"].config_entry = config_entry
    component.register_shutdown()
    await component.async_add_entities([value])
    await hass.async_block_till_done()
    return value, component


@pytest.mark.homeassistant
@pytest.mark.parametrize(
    "observe,bus",
    [
        (True, False),
        (True, True),
        (False, False),
        (False, True),
    ],
)
async def test_setup_and_single_bus_projection_respect_options(hass, observe, bus):
    config_entry = entry(
        {
            "notification_observation": observe,
            "advanced_event_bus": bus,
        }
    )
    config_entry.add_to_hass(hass)
    hub = FakeHub()
    config_entry.runtime_data = coordinator(hub)
    added, exported = [], []
    remove = hass.bus.async_listen("my_verisure_event", exported.append)
    await event_platform.async_setup_entry(hass, config_entry, added.extend)
    assert {item.unique_id for item in added} == (
        {"notification-entry_notifications", "notification-entry_confirmed_results"}
        if observe
        else set()
    )
    component = EntityComponent(logging.getLogger(__name__), "event", hass)
    component._platforms["event"].config_entry = config_entry
    component.register_shutdown()
    await component.async_add_entities(added)
    await hass.async_block_till_done()
    hub.activate()
    value = FakeEvent()
    hub.emit(value)
    await hass.async_block_till_done()
    if observe and bus:
        assert len(exported) == 1
        assert exported[0].data == {
            **value.public_data(),
            "config_entry_id": config_entry.entry_id,
        }
        assert "synthetic-private-value" not in json.dumps(dict(exported[0].data))
    else:
        assert exported == []
    await config_entry._async_process_on_unload(hass)
    for item in tuple(component.entities):
        await component.async_remove_entity(item.entity_id)
    assert hub.listeners == []
    remove()


@pytest.mark.homeassistant
async def test_real_event_stage_filter_privacy_and_unload(hass):
    hub = FakeHub()
    value, component = await add_real_entity(hass, entry(), hub)
    hub.activate()
    assert value.available
    assert not value.should_poll
    assert value.unique_id == "notification-entry_confirmed_results"
    assert value.device_info["identifiers"] == {(DOMAIN, "notification-entry")}
    hub.emit(FakeEvent("photo_reported", "reported"))
    hub.emit(FakeEvent("not-supported", "confirmed"))
    assert hass.states.get(value.entity_id).state == "unknown"
    hub.emit(FakeEvent())
    await hass.async_block_till_done()
    state = hass.states.get(value.entity_id)
    assert state.attributes["event_type"] == "photo_ready"
    assert state.attributes["stage"] == "confirmed"
    assert "synthetic-private-value" not in json.dumps(dict(state.attributes))
    await component.async_remove_entity(value.entity_id)
    assert hub.listeners == []


@pytest.mark.homeassistant
async def test_reported_entity_and_unknown_constructor_stage(hass):
    hub = FakeHub()
    value, _component = await add_real_entity(hass, entry(), hub, "reported")
    hub.activate()
    hub.emit(FakeEvent("photo_reported", "reported"))
    await hass.async_block_till_done()
    assert hass.states.get(value.entity_id).attributes["event_type"] == "photo_reported"
    assert value.unique_id == "notification-entry_notifications"
    with pytest.raises(ValueError):
        event_platform.MyVerisureNotificationEvent(coordinator(hub), entry(), "invalid")


@pytest.mark.homeassistant
async def test_native_received_trigger_keeps_first_and_same_millisecond_events(
    hass, freezer,
):
    hub = FakeHub()
    value, _component = await add_real_entity(hass, entry(), hub)
    trigger = EventReceivedTrigger(
        hass,
        TriggerConfig(
            key="event.received",
            target={"entity_id": [value.entity_id]},
            options={"event_type": ["photo_ready"]},
        ),
    )
    action = Mock()
    remove = await trigger.async_attach_runner(action)
    hub.activate()
    instant = datetime(2026, 11, 23, 2, tzinfo=timezone.utc)
    freezer.move_to(instant)
    hub.emit(FakeEvent(event_id="one"))
    hub.emit(FakeEvent(event_id="two"))
    await hass.async_block_till_done()
    assert action.call_count == 2
    assert action.call_args_list[0].args[0]["from_state"].state == "unknown"
    first = action.call_args_list[0].args[0]["to_state"].state
    second = action.call_args_list[1].args[0]["to_state"].state
    assert first != second
    remove()


@pytest.mark.homeassistant
async def test_restore_does_not_replay_and_next_live_event_triggers(hass):
    hub = FakeHub()
    config_entry = entry()
    identity = "event.notification_entry_confirmed"
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(
                    identity,
                    "2026-11-22T02:00:00+00:00",
                    {"event_type": "photo_ready"},
                    context=Context(user_id="old-local-user"),
                ),
                EventExtraStoredData(
                    "photo_ready", {"event_id": "old-event"}
                ).as_dict(),
            )
        ],
    )
    trigger = EventReceivedTrigger(
        hass,
        TriggerConfig(
            key="event.received",
            target={"entity_id": [identity]},
            options={"event_type": ["photo_ready"]},
        ),
    )
    action = Mock()
    remove = await trigger.async_attach_runner(action)
    value, _component = await add_real_entity(hass, config_entry, hub)
    assert hass.states.get(identity).attributes["event_id"] == "old-event"
    assert hass.states.get(identity).context.user_id is None
    action.assert_not_called()
    hub.emit(FakeEvent(event_id="buffered"))
    hub.activate()
    await hass.async_block_till_done()
    action.assert_not_called()
    hub.emit(FakeEvent(event_id="live"))
    await hass.async_block_till_done()
    assert action.call_count == 1
    assert value.available
    remove()


@pytest.mark.homeassistant
async def test_two_entry_subscriptions_are_isolated(hass):
    first_hub, other_hub = FakeHub(), FakeHub()
    first, _component = await add_real_entity(hass, entry(identity="one"), first_hub)
    other, _other_component = await add_real_entity(
        hass,
        entry(identity="two"),
        other_hub,
    )
    first_hub.activate()
    first_hub.emit(FakeEvent())
    await hass.async_block_till_done()
    assert hass.states.get(first.entity_id).attributes["event_type"] == "photo_ready"
    assert hass.states.get(other.entity_id).state == "unknown"


@pytest.mark.homeassistant
async def test_local_context_reaches_event_bus_and_external_event_clears_it(hass):
    from custom_components.my_verisure.notification_context import NOTIFICATION_CONTEXT

    config_entry = entry({"advanced_event_bus": True})
    config_entry.add_to_hass(hass)
    hub = FakeHub()
    config_entry.runtime_data = coordinator(hub)
    added, exported = [], []
    remove_bus = hass.bus.async_listen("my_verisure_event", exported.append)
    await event_platform.async_setup_entry(hass, config_entry, added.extend)
    component = EntityComponent(logging.getLogger(__name__), "event", hass)
    component._platforms["event"].config_entry = config_entry
    component.register_shutdown()
    for item in added:
        item.entity_id = f"event.context_{item._stage}"
    await component.async_add_entities(added)
    await hass.async_block_till_done()
    value = next(item for item in added if item._stage == "confirmed")
    action = Mock()
    trigger = EventReceivedTrigger(
        hass,
        TriggerConfig(
            key="event.received",
            target={"entity_id": [value.entity_id]},
            options={"event_type": ["photo_ready"]},
        ),
    )
    remove_trigger = await trigger.async_attach_runner(action)
    hub.activate()
    local = Context(user_id="synthetic-local-user")
    token = NOTIFICATION_CONTEXT.set(local)
    try:
        hub.emit(FakeEvent(event_id="local"))
    finally:
        NOTIFICATION_CONTEXT.reset(token)
    await hass.async_block_till_done()
    assert hass.states.get(value.entity_id).context.id == local.id
    assert exported[-1].context.id == local.id
    assert action.call_args.args[2].id == local.id
    hub.emit(FakeEvent(event_id="external"))
    await hass.async_block_till_done()
    state = hass.states.get(value.entity_id)
    assert state.context.user_id is None
    assert state.context.parent_id is None
    assert state.context.id != local.id
    assert exported[-1].context.user_id is None
    assert action.call_args.args[2].user_id is None
    assert "synthetic-local-user" not in json.dumps(dict(state.attributes))
    remove_trigger()
    remove_bus()
    await config_entry._async_process_on_unload(hass)
    for item in tuple(component.entities):
        await component.async_remove_entity(item.entity_id)

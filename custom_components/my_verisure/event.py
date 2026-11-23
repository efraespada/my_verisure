"""Entry-owned notification reports and independently confirmed results.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.application.notifications import (
    CONFIRMED_KINDS,
    REPORTED_KINDS,
    NotificationEvent,
)
from .core.const import (
    CONF_ADVANCED_EVENT_BUS,
    CONF_NOTIFICATION_OBSERVATION,
)
from .device import get_device_info
from .notification_context import NOTIFICATION_CONTEXT

if TYPE_CHECKING:
    from .coordinator import MyVerisureDataUpdateCoordinator

EVENT_NOTIFICATION = "my_verisure_event"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Attach one public projection, independent of the provider connection."""
    if not entry.options.get(CONF_NOTIFICATION_OBSERVATION, True):
        return
    coordinator: MyVerisureDataUpdateCoordinator = entry.runtime_data
    if entry.options.get(CONF_ADVANCED_EVENT_BUS, False):

        @callback
        def forward_event(event: NotificationEvent) -> None:
            hass.bus.async_fire(
                EVENT_NOTIFICATION,
                {
                    **event.public_data(),
                    "config_entry_id": entry.entry_id,
                },
                context=NOTIFICATION_CONTEXT.get(),
            )

        entry.async_on_unload(coordinator.notification_hub.subscribe(forward_event))
    async_add_entities(
        [
            MyVerisureNotificationEvent(coordinator, entry, "reported"),
            MyVerisureNotificationEvent(coordinator, entry, "confirmed"),
        ]
    )


class MyVerisureNotificationEvent(EventEntity):
    """Publish finite typed events without coupling availability to API polling."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        entry: ConfigEntry,
        stage: str,
    ) -> None:
        kinds: tuple[str, ...]
        if stage == "reported":
            suffix, kinds = "notifications", REPORTED_KINDS
        elif stage == "confirmed":
            suffix, kinds = "confirmed_results", CONFIRMED_KINDS
        else:
            raise ValueError("Unsupported notification stage")
        self._stage = stage
        self._hub = coordinator.notification_hub
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_translation_key = suffix
        self._attr_event_types = list(kinds)
        self._attr_device_info = get_device_info(entry)

    async def async_added_to_hass(self) -> None:
        """Core restores the prior display without emitting a new notification."""
        await super().async_added_to_hass()
        self.async_on_remove(self._hub.subscribe(self._received))

    @callback
    def _received(self, event: NotificationEvent) -> None:
        if event.stage != self._stage or event.kind not in self._attr_event_types:
            return
        self.async_set_context(NOTIFICATION_CONTEXT.get() or Context())
        self._trigger_event(event.kind, event.public_data())
        self.async_write_ha_state()

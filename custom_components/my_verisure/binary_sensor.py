"""Platform for My Verisure binary sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.application.alarm_state import AlarmState, analyze_alarm_state
from .core.const import ENTITY_NAMES
from .coordinator import MyVerisureDataUpdateCoordinator
from .device import get_device_info


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up My Verisure binary sensors based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = config_entry.runtime_data

    entities: list[BinarySensorEntity] = []

    # Create alarm status binary sensors
    entities.extend([
        # Binary sensor for internal day alarm
        MyVerisureAlarmBinarySensor(
            coordinator,
            config_entry,
            "internal_day",
            ENTITY_NAMES["binary_sensor_internal_day"],
            BinarySensorDeviceClass.SAFETY,
        ),
        # Binary sensor for internal night alarm
        MyVerisureAlarmBinarySensor(
            coordinator,
            config_entry,
            "internal_night",
            ENTITY_NAMES["binary_sensor_internal_night"],
            BinarySensorDeviceClass.SAFETY,
        ),
        # Binary sensor for internal total alarm
        MyVerisureAlarmBinarySensor(
            coordinator,
            config_entry,
            "internal_total",
            ENTITY_NAMES["binary_sensor_internal_total"],
            BinarySensorDeviceClass.SAFETY,
        ),
        # Binary sensor for external alarm
        MyVerisureAlarmBinarySensor(
            coordinator,
            config_entry,
            "external",
            ENTITY_NAMES["binary_sensor_external"],
            BinarySensorDeviceClass.SAFETY,
        ),
    ])

    if getattr(coordinator, "notification_hub", None) is not None:
        entities.append(MyVerisurePushConnectivitySensor(coordinator, config_entry))
    async_add_entities(entities)


class MyVerisurePushConnectivitySensor(BinarySensorEntity):
    """Expose socket connectivity separately from binding and alarm API health."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_translation_key = "push_connected"

    def __init__(
        self, coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_push_connected"
        self._attr_device_info = get_device_info(config_entry)

    @property
    def is_on(self) -> bool | None:
        data = self._coordinator.notification_diagnostics()
        if data.get("enabled") is False:
            return False
        value = data.get("connected")
        return value if isinstance(value, bool) else None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self._coordinator.notification_hub.subscribe_diagnostics(self._updated)
        )

    @callback
    def _updated(self) -> None:
        self.async_write_ha_state()


class MyVerisureAlarmBinarySensor(BinarySensorEntity):
    """Representation of My Verisure alarm binary sensor."""

    def __init__(
        self,
        coordinator: MyVerisureDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_id: str,
        friendly_name: str,
        device_class: BinarySensorDeviceClass,
    ) -> None:
        """Initialize the alarm binary sensor."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        self.sensor_id = sensor_id

        self._attr_name = friendly_name
        self._attr_unique_id = f"{config_entry.entry_id}_alarm_{sensor_id}"
        self._attr_device_class = device_class
        self._attr_should_poll = False

        # Set device info
        self._attr_device_info = get_device_info(config_entry)

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self.coordinator.data:
            return None
        alarm_status = self.coordinator.data.get("alarm_status")
        if not isinstance(alarm_status, dict):
            return None
        snapshot = analyze_alarm_state(alarm_status)
        if snapshot.state is AlarmState.UNKNOWN:
            return None
        statuses = {
            "internal_day": snapshot.internal_day,
            "internal_night": snapshot.internal_night,
            "internal_total": snapshot.internal_total,
            "external": snapshot.external,
        }
        status = statuses.get(self.sensor_id)
        return None if status is None else status

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_status = self.coordinator.data.get("alarm_status", {})
        if not alarm_status:
            return {}

        return {
            "sensor_type": self.sensor_id,
            "last_updated": self.coordinator.data.get("last_updated"),
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

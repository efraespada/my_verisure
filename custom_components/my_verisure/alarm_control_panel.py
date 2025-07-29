"""Platform for My Verisure alarm control panel."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator

# My Verisure alarm states mapping
VERISURE_TO_HA_STATES = {
    # Standard states
    "DISARMED": STATE_ALARM_DISARMED,
    "ARMED_AWAY": STATE_ALARM_ARMED_AWAY,
    "ARMED_HOME": STATE_ALARM_ARMED_HOME,
    "ARMED_NIGHT": STATE_ALARM_ARMED_NIGHT,
    "TRIGGERED": STATE_ALARM_TRIGGERED,
    
    # My Verisure specific states (from services response)
    "DARM": STATE_ALARM_DISARMED,           # DESCONECTAR
    "ARM": STATE_ALARM_ARMED_AWAY,          # CONECTAR (Total)
    "ARMDAY": STATE_ALARM_ARMED_HOME,       # ARMADO DIA (Interior Parcial Día)
    "ARMNIGHT": STATE_ALARM_ARMED_NIGHT,    # ARMADO NOCHE (Interior Parcial Noche)
    "PERI": STATE_ALARM_ARMED_AWAY,         # PERIMETRAL (Exterior)
    "ARMINTFPART": STATE_ALARM_ARMED_HOME,  # Armado Interior Parcial
    "ARMPARTFINT": STATE_ALARM_ARMED_HOME,  # Armado Parcial Interior
    
    # Legacy mappings for compatibility
    "PARTIAL_DAY": STATE_ALARM_ARMED_HOME,
    "PARTIAL_NIGHT": STATE_ALARM_ARMED_NIGHT,
    "TOTAL": STATE_ALARM_ARMED_AWAY,
    "PERIMETRAL": STATE_ALARM_ARMED_AWAY,
}

HA_TO_VERISURE_STATES = {
    STATE_ALARM_DISARMED: "DARM",           # DESCONECTAR
    STATE_ALARM_ARMED_AWAY: "ARM",          # CONECTAR (Total)
    STATE_ALARM_ARMED_HOME: "ARMDAY",       # ARMADO DIA (Interior Parcial Día)
    STATE_ALARM_ARMED_NIGHT: "ARMNIGHT",    # ARMADO NOCHE (Interior Parcial Noche)
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up My Verisure alarm control panel based on a config entry."""
    coordinator: MyVerisureDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    # Create alarm control panel entity
    async_add_entities([MyVerisureAlarmControlPanel(coordinator, config_entry)])


class MyVerisureAlarmControlPanel(AlarmControlPanelEntity):
    """Representation of a My Verisure alarm control panel."""

    def __init__(
        self, coordinator: MyVerisureDataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Initialize the alarm control panel."""
        self.coordinator = coordinator
        self.config_entry = config_entry
        # We'll update the name later when we have installation data
        self._attr_name = f"My Verisure Alarm"
        self._attr_unique_id = f"{config_entry.entry_id}_alarm"
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_NIGHT
            | AlarmControlPanelEntityFeature.DISARM
        )

    @property
    def name(self) -> str:
        """Return the name of the alarm."""
        if not self.coordinator.data:
            return self._attr_name

        services_data = self.coordinator.data.get("services", {})
        installation_info = services_data.get("installation", {})
        alias = installation_info.get("alias", "Unknown")
        
        # Clean up the alias (remove extra commas and spaces)
        if alias and alias != "Unknown":
            # Remove extra commas and clean up
            alias = alias.replace(", ,", ",").replace("  ", " ").strip()
            if alias.endswith(","):
                alias = alias[:-1].strip()
        
        return f"My Verisure Alarm ({alias})"

    @property
    def state(self) -> str | None:
        """Return the state of the alarm."""
        if not self.coordinator.data:
            return None

        alarm_data = self.coordinator.data.get("alarm", {})
        verisure_state = alarm_data.get("state", "UNKNOWN")
        
        LOGGER.warning("Alarm state from Verisure: %s", verisure_state)
        
        # Map Verisure state to Home Assistant state
        ha_state = VERISURE_TO_HA_STATES.get(verisure_state.upper(), STATE_ALARM_DISARMED)
        LOGGER.warning("Mapped to HA state: %s", ha_state)
        
        return ha_state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_data = self.coordinator.data.get("alarm", {})
        device = alarm_data.get("device", {})
        
        # Get alarm data (now includes services info)
        alarm_data = self.coordinator.data.get("alarm", {})
        available_commands = alarm_data.get("available_commands", [])
        alarm_services = alarm_data.get("services", [])
        
        # Convert services list to dict for backward compatibility
        services_dict = {}
        for service in alarm_services:
            request = service.get("request", "")
            services_dict[request] = {
                "id": service.get("idService", ""),
                "name": service.get("request", ""),
                "active": service.get("active", False)
            }
        
        # Get installation info from services
        services_data = self.coordinator.data.get("services", {})
        installation_info = services_data.get("installation", {})
        
        return {
            "verisure_state": alarm_data.get("state", "UNKNOWN"),
            "device_id": device.get("id", "Unknown"),
            "device_type": device.get("type", "Unknown"),
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
            "installation_alias": installation_info.get("alias", "Unknown"),
            "installation_status": installation_info.get("status", "Unknown"),
            "installation_panel": installation_info.get("panel", "Unknown"),
            "available_commands": available_commands,
            "services": services_dict,
        }

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        LOGGER.warning("Disarming alarm (DARM - DESCONECTAR)...")
        try:
            # TODO: Implement actual disarm command to My Verisure API
            # await self.coordinator.client.send_alarm_command("DARM")
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to disarm alarm: %s", e)

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        LOGGER.warning("Arming alarm away (ARM - CONECTAR Total)...")
        try:
            # TODO: Implement actual arm away command to My Verisure API
            # await self.coordinator.client.send_alarm_command("ARM")
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to arm alarm away: %s", e)

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        LOGGER.warning("Arming alarm home (ARMDAY - ARMADO DIA)...")
        try:
            # TODO: Implement actual arm home command to My Verisure API
            # await self.coordinator.client.send_alarm_command("ARMDAY")
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to arm alarm home: %s", e)

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        LOGGER.warning("Arming alarm night (ARMNIGHT - ARMADO NOCHE)...")
        try:
            # TODO: Implement actual arm night command to My Verisure API
            # await self.coordinator.client.send_alarm_command("ARMNIGHT")
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to arm alarm night: %s", e)

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
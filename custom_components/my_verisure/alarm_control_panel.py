"""Platform for My Verisure alarm control panel."""

from __future__ import annotations

from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER, ENTITY_NAMES
from .coordinator import MyVerisureDataUpdateCoordinator
from .device import get_device_info

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
        # Use a simple name and unique_id
        self._attr_name = ENTITY_NAMES["alarm_control_panel"]
        self._attr_unique_id = "my_verisure"
        self._attr_code_format = None  # No code required
        self._attr_code_arm_required = False  # No code required for arming
        self._attr_code_disarm_required = False  # No code required for disarming
        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT
            | AlarmControlPanelEntityFeature.ARM_HOME
        )
        # Track transition state for ARMING/DISARMING feedback
        self._transition_state = None

        # Set device info
        self._attr_device_info = get_device_info(config_entry)

    @property
    def name(self) -> str:
        """Return the name of the alarm."""
        return ENTITY_NAMES["alarm_control_panel"]

    def _analyze_alarm_states(
        self, alarm_data: dict
    ) -> tuple[AlarmControlPanelState, dict]:
        """
        Analyze alarm data and return the primary state and detailed state information.

        Returns:
            tuple: (primary_state, detailed_states_dict)
        """
        if not alarm_data:
            return AlarmControlPanelState.DISARMED, {}

        # Parse the JSON structure with internal/external sections
        internal = alarm_data.get("internal", {})
        external = alarm_data.get("external", {})

        # Check internal states
        internal_day = internal.get("day", {}).get("status", False)
        internal_night = internal.get("night", {}).get("status", False)
        internal_total = internal.get("total", {}).get("status", False)

        # Check external state
        external_status = external.get("status", False)

        # Create detailed state information
        detailed_states = {
            "internal_day": internal_day,
            "internal_night": internal_night,
            "internal_total": internal_total,
            "external": external_status,
            "active_alarms": []
        }

        # Determine which alarms are active
        if internal_total:
            detailed_states["active_alarms"].append("Internal Total")
        if internal_day:
            detailed_states["active_alarms"].append("Internal Day")
        if internal_night:
            detailed_states["active_alarms"].append("Internal Night")
        if external_status:
            detailed_states["active_alarms"].append("External")

        # Determine primary state based on priority
        # Priority order: Total > Night > Day > External > Disarmed
        if internal_total:
            primary_state = AlarmControlPanelState.ARMED_AWAY
        elif internal_night:
            primary_state = AlarmControlPanelState.ARMED_NIGHT
        elif internal_day:
            primary_state = AlarmControlPanelState.ARMED_NIGHT
        elif external_status:
            # Map external to home
            primary_state = AlarmControlPanelState.ARMED_HOME
        else:
            primary_state = AlarmControlPanelState.DISARMED

        return primary_state, detailed_states

    @property
    def alarm_state(self) -> AlarmControlPanelState | None:
        """Return the state of the alarm."""
        # If we're in a transition state, return it immediately
        if self._transition_state:
            LOGGER.warning("Returning transition state: %s", self._transition_state)
            return self._transition_state

        if not self.coordinator.data:
            LOGGER.warning("No coordinator data available")
            return None

        alarm_data = self.coordinator.data.get("alarm_status", {})
        LOGGER.warning("Raw alarm data: %s", alarm_data)

        primary_state, detailed_states = self._analyze_alarm_states(alarm_data)

        LOGGER.warning("Primary state: %s", primary_state)
        LOGGER.warning("Active alarms: %s", detailed_states.get("active_alarms", []))

        return primary_state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}

        alarm_data = self.coordinator.data.get("alarm_status", {})

        # Get detailed state analysis
        _, detailed_states = self._analyze_alarm_states(alarm_data)

        # Get installation info from services
        services_data = self.coordinator.data.get("services", {})
        installation_info = services_data.get("installation", {})

        attributes = {
            "installation_id": self.config_entry.data.get("installation_id", "Unknown"),
            "installation_alias": installation_info.get("alias", "Unknown"),
            "installation_status": installation_info.get("status", "Unknown"),
            "installation_panel": installation_info.get("panel", "Unknown"),
        }

        # Add detailed alarm state information
        attributes.update({
            "internal_day_status": detailed_states.get("internal_day", False),
            "internal_night_status": detailed_states.get("internal_night", False),
            "internal_total_status": detailed_states.get("internal_total", False),
            "external_status": detailed_states.get("external", False),
            "active_alarms": detailed_states.get("active_alarms", []),
            "alarm_count": len(detailed_states.get("active_alarms", [])),
        })

        return attributes

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        LOGGER.warning("Disarming alarm (DARM - DESCONECTAR)...")
        
        # Set transition state
        self._transition_state = AlarmControlPanelState.DISARMING
        self.async_write_ha_state()
        
        try:
            installation_id = self.config_entry.data.get("installation_id")
            if installation_id:
                success = await self.coordinator.client.disarm_alarm(installation_id)
                if success:
                    LOGGER.info("Alarm disarmed successfully")
                else:
                    LOGGER.error("Failed to disarm alarm")
            else:
                LOGGER.error("No installation ID available")
            
            # Clear transition state and refresh
            self._transition_state = None
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to disarm alarm: %s", e)
            # Clear transition state on error
            self._transition_state = None
            self.async_write_ha_state()

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        LOGGER.warning("Arming alarm away (ARM - CONECTAR Total)...")

        # Set transition state
        self._transition_state = AlarmControlPanelState.ARMING
        self.async_write_ha_state()

        try:
            installation_id = self.config_entry.data.get("installation_id")
            if installation_id:
                success = await self.coordinator.client.arm_alarm_away(installation_id)
                if success:
                    LOGGER.info("Alarm armed away successfully")
                else:
                    LOGGER.error("Failed to arm alarm away")
            else:
                LOGGER.error("No installation ID available")

            # Clear transition state and refresh
            self._transition_state = None
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to arm alarm away: %s", e)
            # Clear transition state on error
            self._transition_state = None
            self.async_write_ha_state()

    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Send arm home command."""
        LOGGER.warning("Arming alarm home (ARMDAY - ARMADO DIA)...")

        # Set transition state
        self._transition_state = AlarmControlPanelState.ARMING
        self.async_write_ha_state()

        try:
            installation_id = self.config_entry.data.get("installation_id")
            if installation_id:
                success = await self.coordinator.client.arm_alarm_home(installation_id)
                if success:
                    LOGGER.info("Alarm armed home successfully")
                else:
                    LOGGER.error("Failed to arm alarm home")
            else:
                LOGGER.error("No installation ID available")

            # Clear transition state and refresh
            self._transition_state = None
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to arm alarm home: %s", e)
            # Clear transition state on error
            self._transition_state = None
            self.async_write_ha_state()

    async def async_alarm_arm_night(self, code: str | None = None) -> None:
        """Send arm night command."""
        LOGGER.warning("Arming alarm night (ARMNIGHT - ARMADO NOCHE)...")

        # Set transition state
        self._transition_state = AlarmControlPanelState.ARMING
        self.async_write_ha_state()

        try:
            installation_id = self.config_entry.data.get("installation_id")
            if installation_id:
                success = await self.coordinator.client.arm_alarm_night(installation_id)
                if success:
                    LOGGER.info("Alarm armed night successfully")
                else:
                    LOGGER.error("Failed to arm alarm night")
            else:
                LOGGER.error("No installation ID available")

            # Clear transition state and refresh
            self._transition_state = None
            await self.coordinator.async_request_refresh()
        except Exception as e:
            LOGGER.error("Failed to arm alarm night: %s", e)
            # Clear transition state on error
            self._transition_state = None
            self.async_write_ha_state()

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
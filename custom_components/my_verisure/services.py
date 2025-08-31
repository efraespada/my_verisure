"""Services for the My Verisure integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN, LOGGER

# Service schemas
SERVICE_ARM_AWAY_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})

SERVICE_ARM_HOME_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})

SERVICE_ARM_NIGHT_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})

SERVICE_DISARM_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})

SERVICE_GET_STATUS_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})




async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for My Verisure."""
    
    async def async_arm_away_service(call: ServiceCall) -> None:
        """Service to arm the alarm away."""
        installation_id = call.data["installation_id"]
        
        # Find the coordinator for this installation
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                try:
                    success = await coordinator.client.arm_alarm_away(installation_id)
                    if success:
                        LOGGER.info("Alarm armed away successfully via service")
                    else:
                        LOGGER.error("Failed to arm alarm away via service")
                except Exception as e:
                    LOGGER.error("Error arming alarm away via service: %s", e)
                break
        else:
            LOGGER.error("Installation %s not found", installation_id)

    async def async_arm_home_service(call: ServiceCall) -> None:
        """Service to arm the alarm home."""
        installation_id = call.data["installation_id"]
        
        # Find the coordinator for this installation
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                try:
                    success = await coordinator.client.arm_alarm_home(installation_id)
                    if success:
                        LOGGER.info("Alarm armed home successfully via service")
                    else:
                        LOGGER.error("Failed to arm alarm home via service")
                except Exception as e:
                    LOGGER.error("Error arming alarm home via service: %s", e)
                break
        else:
            LOGGER.error("Installation %s not found", installation_id)

    async def async_arm_night_service(call: ServiceCall) -> None:
        """Service to arm the alarm night."""
        installation_id = call.data["installation_id"]
        
        # Find the coordinator for this installation
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                try:
                    success = await coordinator.client.arm_alarm_night(installation_id)
                    if success:
                        LOGGER.info("Alarm armed night successfully via service")
                    else:
                        LOGGER.error("Failed to arm alarm night via service")
                except Exception as e:
                    LOGGER.error("Error arming alarm night via service: %s", e)
                break
        else:
            LOGGER.error("Installation %s not found", installation_id)

    async def async_disarm_service(call: ServiceCall) -> None:
        """Service to disarm the alarm."""
        installation_id = call.data["installation_id"]
        code = call.data.get("code")
        
        # Find the coordinator for this installation
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                try:
                    success = await coordinator.client.disarm_alarm(installation_id)
                    if success:
                        LOGGER.info("Alarm disarmed successfully via service")
                    else:
                        LOGGER.error("Failed to disarm alarm via service")
                except Exception as e:
                    LOGGER.error("Error disarming alarm via service: %s", e)
                break
        else:
            LOGGER.error("Installation %s not found", installation_id)

    async def async_get_status_service(call: ServiceCall) -> None:
        """Service to get alarm status."""
        installation_id = call.data["installation_id"]
        
        # Find the coordinator for this installation
        for entry_id, coordinator in hass.data[DOMAIN].items():
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                try:
                    await coordinator.async_request_refresh()
                    LOGGER.info("Alarm status refreshed via service")
                except Exception as e:
                    LOGGER.error("Error refreshing alarm status via service: %s", e)
                break
        else:
            LOGGER.error("Installation %s not found", installation_id)



    # Register services
    hass.services.async_register(
        DOMAIN,
        "arm_away",
        async_arm_away_service,
        schema=SERVICE_ARM_AWAY_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        "arm_home",
        async_arm_home_service,
        schema=SERVICE_ARM_HOME_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        "arm_night",
        async_arm_night_service,
        schema=SERVICE_ARM_NIGHT_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        "disarm",
        async_disarm_service,
        schema=SERVICE_DISARM_SCHEMA,
    )
    
    hass.services.async_register(
        DOMAIN,
        "get_status",
        async_get_status_service,
        schema=SERVICE_GET_STATUS_SCHEMA,
    )
    



async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for My Verisure."""
    hass.services.async_remove(DOMAIN, "arm_away")
    hass.services.async_remove(DOMAIN, "arm_home")
    hass.services.async_remove(DOMAIN, "arm_night")
    hass.services.async_remove(DOMAIN, "disarm")
    hass.services.async_remove(DOMAIN, "get_status")
 
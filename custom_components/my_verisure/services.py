"""Services for the My Verisure integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .core.application.alarm_service import AlarmServiceDispatcher
from .core.application.exceptions import MyVerisureError
from .core.const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator

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

SERVICE_REFRESH_CAMERA_IMAGES_SCHEMA = vol.Schema({
    vol.Required("installation_id"): cv.string,
})


def _update_alarm_panel_state(coordinator: MyVerisureDataUpdateCoordinator) -> None:
    """Update the alarm control panel state via coordinator."""
    try:
        coordinator.clear_alarm_transition_state()
        LOGGER.warning("Updated alarm control panel state via coordinator")
    except Exception:
        LOGGER.error("Error updating alarm panel state")


def _iter_coordinators(hass: HomeAssistant):
    """Yield loaded My Verisure coordinators from config entries."""
    for domain_entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = getattr(domain_entry, "runtime_data", None)
        if isinstance(coordinator, MyVerisureDataUpdateCoordinator):
            yield coordinator


def _update_button_state(coordinator: MyVerisureDataUpdateCoordinator) -> None:
    """Update the button state via coordinator."""
    try:
        coordinator.clear_button_executing_state()
        LOGGER.warning("Updated button state via coordinator")
    except Exception:
        LOGGER.error("Error updating button state")


async def _dispatch_alarm_service(
    hass: HomeAssistant,
    installation_id: str,
    command: str,
    operation_name: str,
) -> None:
    """Dispatch an alarm operation and normalize adapter-side state updates."""
    coordinators = tuple(_iter_coordinators(hass))
    dispatcher = AlarmServiceDispatcher(coordinators)
    result = await dispatcher.dispatch(installation_id, command)
    coordinator = next(
        (
            item
            for item in coordinators
            if item.config_entry.data.get("installation_id") == installation_id
        ),
        None,
    )

    if coordinator is None:
        raise MyVerisureError("Installation not found")

    if result.success:
        LOGGER.warning("Alarm %s successfully via service", operation_name)
    else:
        LOGGER.error("Failed to %s alarm via service", operation_name)
    _update_alarm_panel_state(coordinator)
    if not result.success:
        raise MyVerisureError(result.message or "Alarm command failed")


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for My Verisure."""

    async def async_arm_away_service(call: ServiceCall) -> None:
        """Service to arm the alarm away."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service arm_away called")
        await _dispatch_alarm_service(
            hass, installation_id, "async_arm_away", "arm away"
        )

    async def async_arm_home_service(call: ServiceCall) -> None:
        """Service to arm the alarm home."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service arm_home called")
        await _dispatch_alarm_service(
            hass, installation_id, "async_arm_home", "arm home"
        )

    async def async_arm_night_service(call: ServiceCall) -> None:
        """Service to arm the alarm night."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service arm_night called")
        await _dispatch_alarm_service(
            hass, installation_id, "async_arm_night", "arm night"
        )

    async def async_disarm_service(call: ServiceCall) -> None:
        """Service to disarm the alarm."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service disarm called")
        await _dispatch_alarm_service(hass, installation_id, "async_disarm", "disarm")

    async def async_get_status_service(call: ServiceCall) -> None:
        """Service to get alarm status."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service get_status called")

        # Find the coordinator for this installation
        for coordinator in _iter_coordinators(hass):
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                LOGGER.warning(
                    "Found coordinator; calling async_request_refresh"
                )
                try:
                    await coordinator.async_request_refresh()
                    LOGGER.warning("Alarm status refreshed via service")
                except Exception:
                    LOGGER.error("Error refreshing alarm status via service")
                break
        else:
            LOGGER.error("Installation not found")

    async def async_refresh_camera_images_service(call: ServiceCall) -> None:
        """Service to refresh camera images."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service refresh_camera_images called")

        # Find the coordinator for this installation
        for coordinator in _iter_coordinators(hass):
            if coordinator.config_entry.data.get("installation_id") == installation_id:
                LOGGER.warning(
                    "Found coordinator; calling async_refresh_camera_images"
                )
                try:
                    await coordinator.async_refresh_camera_images()
                    LOGGER.warning("Camera images refreshed via service")
                    _update_button_state(coordinator)
                except Exception:
                    LOGGER.error("Error refreshing camera images via service")
                    _update_button_state(coordinator)
                break
        else:
            LOGGER.error("Installation not found")

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

    hass.services.async_register(
        DOMAIN,
        "refresh_camera_images",
        async_refresh_camera_images_service,
        schema=SERVICE_REFRESH_CAMERA_IMAGES_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for My Verisure."""
    hass.services.async_remove(DOMAIN, "arm_away")
    hass.services.async_remove(DOMAIN, "arm_home")
    hass.services.async_remove(DOMAIN, "arm_night")
    hass.services.async_remove(DOMAIN, "disarm")
    hass.services.async_remove(DOMAIN, "get_status")
    hass.services.async_remove(DOMAIN, "refresh_camera_images")

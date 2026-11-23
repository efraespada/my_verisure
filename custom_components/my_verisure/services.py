"""Services for the My Verisure integration."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_registry as er
import voluptuous as vol

from .core.application.alarm_service import AlarmServiceDispatcher
from .core.application.exceptions import (
    MyVerisureError, MyVerisureAuthenticationError, MyVerisureServiceBlockedError,
)
from .core.const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator
from .camera import camera_unique_id
from .notification_context import notification_service_context

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
    vol.Optional("camera_entity_id"): cv.entity_id,
})


def _selected_camera_identifier(coordinator, entity_id: str) -> str:
    """Resolve only an existing camera owned by the selected installation."""
    entity = er.async_get(coordinator.hass).async_get(entity_id)
    if (
        entity is None or entity.domain != "camera" or entity.platform != DOMAIN
        or entity.config_entry_id != coordinator.config_entry.entry_id
    ):
        raise HomeAssistantError("Selected camera unavailable")
    devices = (coordinator.data or {}).get("detailed_installation", {}).get("installation", {}).get("devices", [])
    matches = [
        device for device in devices
        if device.get("type") in {"YP", "YR"}
        and camera_unique_id(coordinator.config_entry.entry_id, device) == entity.unique_id
    ]
    if len(matches) != 1:
        raise HomeAssistantError("Selected camera unavailable")
    return f"{matches[0]['type']}{int(matches[0]['code']):02d}"


def _camera_refresh_error(error: Exception) -> HomeAssistantError:
    """Expose a translated HA error without provider payloads or credentials."""
    key = "camera_refresh_failed"
    message = "Camera image refresh failed"
    if isinstance(error, MyVerisureServiceBlockedError):
        key = "camera_service_blocked"
        message = "Verisure temporarily blocked requests; wait before retrying"
    elif isinstance(error, MyVerisureAuthenticationError):
        key = "camera_authentication_required"
        message = "Verisure authentication is required"
    return HomeAssistantError(
        message, translation_domain=DOMAIN, translation_key=key,
    )


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

    @notification_service_context
    async def async_arm_away_service(call: ServiceCall) -> None:
        """Service to arm the alarm away."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service arm_away called")
        await _dispatch_alarm_service(
            hass, installation_id, "async_arm_away", "arm away"
        )

    @notification_service_context
    async def async_arm_home_service(call: ServiceCall) -> None:
        """Service to arm the alarm home."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service arm_home called")
        await _dispatch_alarm_service(
            hass, installation_id, "async_arm_home", "arm home"
        )

    @notification_service_context
    async def async_arm_night_service(call: ServiceCall) -> None:
        """Service to arm the alarm night."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service arm_night called")
        await _dispatch_alarm_service(
            hass, installation_id, "async_arm_night", "arm night"
        )

    @notification_service_context
    async def async_disarm_service(call: ServiceCall) -> None:
        """Service to disarm the alarm."""
        installation_id = call.data["installation_id"]
        LOGGER.warning("Service disarm called")
        await _dispatch_alarm_service(hass, installation_id, "async_disarm", "disarm")

    @notification_service_context
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

    @notification_service_context
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
                    selected = call.data.get("camera_entity_id")
                    if selected is None:
                        await coordinator.async_refresh_camera_images()
                    else:
                        await coordinator.async_refresh_camera_images(
                            camera_identifier=_selected_camera_identifier(coordinator, selected)
                        )
                    LOGGER.warning("Camera images refreshed via service")
                except HomeAssistantError:
                    raise
                except Exception as error:
                    LOGGER.error("Camera refresh failed (%s)", type(error).__name__)
                    raise _camera_refresh_error(error) from None
                finally:
                    _update_button_state(coordinator)
                break
        else:
            raise HomeAssistantError("Installation not found")

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

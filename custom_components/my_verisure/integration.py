"""Home Assistant integration for My Verisure."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed

from .core.const import DOMAIN, LOGGER
from .coordinator import MyVerisureDataUpdateCoordinator
from .device import async_setup_device
from .services import async_setup_services, async_unload_services

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.CAMERA,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My Verisure from a config entry."""
    LOGGER.info("Setting up My Verisure integration")

    coordinator = MyVerisureDataUpdateCoordinator(hass, entry=entry)

    # Load session asynchronously
    await coordinator.async_load_session()

    # Check if we have a session (even if expired or empty)
    if coordinator.get_session_hash() is None:
        LOGGER.info("No session found — will attempt authentication on first update")
    elif not coordinator.has_valid_session():
        LOGGER.info("Session expired — automatic refresh will be attempted on updates")
    else:
        LOGGER.info("Valid session found — integration ready")

    # Try to load cached data before attempting first refresh
    cached_data = coordinator.load_alarm_info()
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryAuthFailed:
        LOGGER.error("Authentication failed - invalid credentials")
        raise
    except Exception as ex:
        # If first refresh fails but we have cached data, use it and continue
        if cached_data:
            LOGGER.warning(
                "First refresh failed (%s) but using cached data - integration will continue "
                "and retry on next update cycle",
                str(ex),
            )
            coordinator.data = cached_data
        else:
            LOGGER.error(
                "First refresh failed and no cached data available: %s",
                ex,
            )
            raise

    entry.runtime_data = coordinator

    hass.data.setdefault(DOMAIN, {})

    # Set up the device
    await async_setup_device(hass, entry)

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services (only once)
    if not hass.data[DOMAIN].get("services_setup"):
        await async_setup_services(hass)
        hass.data[DOMAIN]["services_setup"] = True

    # Update options
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the My Verisure component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload My Verisure config entry."""
    LOGGER.info("Unloading My Verisure integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    # Note: do not call coordinator.async_cleanup() here — clear_dependencies()
    # is global and would break other loaded my_verisure config entries.

    remaining_entries = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id
    ]
    if not remaining_entries:
        await async_unload_services(hass)
        hass.data.pop(DOMAIN, None)

    return True 
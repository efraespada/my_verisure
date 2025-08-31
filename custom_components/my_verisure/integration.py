"""Home Assistant integration for My Verisure."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .coordinator import MyVerisureDataUpdateCoordinator
from .device import async_setup_device
from .services import async_setup_services, async_unload_services

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up My Verisure from a config entry."""
    LOGGER.warning("Setting up My Verisure integration")

    coordinator = MyVerisureDataUpdateCoordinator(hass, entry=entry)

    # Load session asynchronously
    await coordinator.async_load_session()

    # Check if we have a session (even if expired or empty)
    if coordinator.client._hash is None:
        LOGGER.warning("No session found - integration will start and attempt automatic authentication during first data update")
    elif not coordinator.can_operate_without_login():
        LOGGER.warning("Session is expired but integration will start - automatic refresh will be attempted during data updates")
    else:
        LOGGER.warning("Valid session found - integration ready")

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

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
    # Propagate configuration change
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Update coordinator with new scan interval
    scan_interval_minutes = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    try:
        scan_interval_minutes = int(scan_interval_minutes)
    except (ValueError, TypeError):
        scan_interval_minutes = DEFAULT_SCAN_INTERVAL
    
    from datetime import timedelta
    new_scan_interval = timedelta(minutes=scan_interval_minutes)
    
    LOGGER.warning("Updating coordinator scan interval to %s minutes", scan_interval_minutes)
    coordinator.update_interval = new_scan_interval
    
    coordinator.async_update_listeners()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload My Verisure config entry."""
    LOGGER.warning("Unloading My Verisure integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    del hass.data[DOMAIN][entry.entry_id]

    # Unload services if no more entries
    if not hass.data[DOMAIN]:
        await async_unload_services(hass)
        del hass.data[DOMAIN]

    return True 
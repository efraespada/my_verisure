"""Device support for My Verisure."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo

from .core.const import DOMAIN, DEVICE_INFO


def get_device_info(config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for My Verisure."""
    entry_id = config_entry.entry_id

    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="My Verisure Alarm",
        manufacturer=DEVICE_INFO["manufacturer"],
        model=DEVICE_INFO["model"],
        sw_version=DEVICE_INFO["sw_version"],
        configuration_url=DEVICE_INFO["configuration_url"],
    )


async def async_setup_device(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Set up the My Verisure device."""
    device_registry = dr.async_get(hass)
    
    entry_id = config_entry.entry_id

    # Create or update the device
    device_registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, entry_id)},
        name="My Verisure Alarm",
        manufacturer=DEVICE_INFO["manufacturer"],
        model=DEVICE_INFO["model"],
        sw_version=DEVICE_INFO["sw_version"],
        configuration_url=DEVICE_INFO["configuration_url"],
    ) 
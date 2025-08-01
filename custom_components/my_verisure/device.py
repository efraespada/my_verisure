"""Device support for My Verisure."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DEVICE_INFO


def get_device_info(config_entry: ConfigEntry) -> DeviceInfo:
    """Get device info for My Verisure."""
    installation_id = config_entry.data.get("installation_id", "Unknown")
    
    return DeviceInfo(
        identifiers={(DOMAIN, installation_id)},
        name=f"My Verisure Alarm ({installation_id})",
        manufacturer=DEVICE_INFO["manufacturer"],
        model=DEVICE_INFO["model"],
        sw_version=DEVICE_INFO["sw_version"],
        configuration_url=DEVICE_INFO["configuration_url"],
    )


async def async_setup_device(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Set up the My Verisure device."""
    device_registry = dr.async_get(hass)
    
    installation_id = config_entry.data.get("installation_id", "Unknown")
    
    # Create or update the device
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, installation_id)},
        name=f"My Verisure Alarm ({installation_id})",
        manufacturer=DEVICE_INFO["manufacturer"],
        model=DEVICE_INFO["model"],
        sw_version=DEVICE_INFO["sw_version"],
        configuration_url=DEVICE_INFO["configuration_url"],
    ) 
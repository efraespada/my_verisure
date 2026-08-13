"""Pure camera device selection rules shared by camera use cases."""

from __future__ import annotations

from collections.abc import Iterable

from ..api.models.domain.device import Device

CAMERA_DEVICE_TYPES = frozenset({"YR", "YP"})


def camera_devices(devices: Iterable[Device]) -> list[Device]:
    """Return active Verisure camera devices in source order."""
    return [
        device
        for device in devices
        if device.is_active and device.type in CAMERA_DEVICE_TYPES
    ]


def camera_identifier(device: Device) -> str:
    """Build the public camera identifier used by image repositories."""
    return f"{device.type}{int(device.code):02d}"

"""Semantic storage seam and snapshot selection for camera placeholders.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from collections.abc import Mapping
from typing import Any, Protocol

from .camera_devices import CAMERA_DEVICE_TYPES
from .models.camera_refresh import CameraRefresh


class CameraPlaceholderStore(Protocol):
    """Ensure local placeholders without querying the alarm provider."""

    async def ensure_placeholders(
        self, camera_identifiers: tuple[str, ...]
    ) -> CameraRefresh:
        """Keep existing committed images or atomically create placeholders."""


def snapshot_camera_identifiers(snapshot: Mapping[str, Any]) -> tuple[str, ...]:
    """Select active cameras from the snapshot already read by the caller."""
    installation = snapshot.get("detailed_installation", {})
    if not isinstance(installation, Mapping):
        return ()
    installation = installation.get("installation", {})
    if not isinstance(installation, Mapping):
        return ()
    devices = installation.get("devices", [])
    if not isinstance(devices, list):
        return ()
    identifiers: dict[str, None] = {}
    for device in devices:
        if not isinstance(device, Mapping):
            continue
        kind, code = device.get("type"), device.get("code")
        if (
            not isinstance(kind, str)
            or kind not in CAMERA_DEVICE_TYPES
            or device.get("is_active") is False
        ):
            continue
        if isinstance(code, bool) or not isinstance(code, (str, int)):
            continue
        try:
            number = int(code)
        except ValueError:
            continue
        if number >= 0:
            identifiers[f"{kind}{number:02d}"] = None
    return tuple(identifiers)

"""Provider-independent camera image projections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CameraThumbnail:
    """Validated thumbnail metadata and encoded image."""

    id_signal: str
    signal_type: str
    device_alias: str
    timestamp: str
    image: str


@dataclass(frozen=True)
class CameraPhotoSet:
    """Validated photo images returned for one camera device."""

    images: list[dict[str, str]]

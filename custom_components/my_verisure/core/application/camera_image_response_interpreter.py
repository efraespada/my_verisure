"""Pure interpretation of camera image retrieval responses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class CameraImageResponseError(ValueError):
    """Provider response cannot be interpreted under the image contract."""


@dataclass(frozen=True)
class CameraThumbnail:
    """Thumbnail metadata and encoded image returned by the provider."""

    id_signal: str
    signal_type: str
    device_alias: str
    timestamp: str
    image: str


@dataclass(frozen=True)
class CameraPhotoSet:
    """Photo images returned for one camera device."""

    images: list[dict[str, str]]


def interpret_thumbnail_response(result: object, *, default_zone: str) -> CameraThumbnail:
    """Interpret the xSGetThumbnail GraphQL envelope."""
    data = _require_data(result, "thumbnail")
    response = data.get("xSGetThumbnail")
    if not isinstance(response, dict) or not response:
        raise CameraImageResponseError("Invalid response from thumbnail service")

    id_signal = response.get("idSignal")
    if not isinstance(id_signal, str) or not id_signal:
        raise CameraImageResponseError("No idSignal received from thumbnail query")

    return CameraThumbnail(
        id_signal=id_signal,
        signal_type=_optional_string(response.get("signalType"), "16"),
        device_alias=_optional_string(response.get("deviceAlias"), default_zone),
        timestamp=_optional_string(response.get("timestamp"), ""),
        image=_optional_string(response.get("image"), ""),
    )


def interpret_photo_response(result: object) -> CameraPhotoSet:
    """Interpret the xSGetPhotoImages GraphQL envelope."""
    data = _require_data(result, "photo images")
    response = data.get("xSGetPhotoImages")
    if not isinstance(response, dict) or not response:
        raise CameraImageResponseError("Invalid response from photo images service")

    devices = response.get("devices")
    if not isinstance(devices, list) or not devices:
        return CameraPhotoSet(images=[])

    first_device = devices[0]
    if not isinstance(first_device, dict):
        raise CameraImageResponseError("Invalid camera device in photo images response")

    raw_images = first_device.get("images", [])
    if not isinstance(raw_images, list):
        raise CameraImageResponseError("Invalid images collection in photo images response")

    images: list[dict[str, str]] = []
    for raw_image in raw_images:
        if not isinstance(raw_image, dict):
            continue
        image_id = raw_image.get("id", "unknown")
        image_data = raw_image.get("image", "")
        if isinstance(image_id, str) and isinstance(image_data, str):
            images.append({"id": image_id, "image": image_data})

    return CameraPhotoSet(images=images)


def _require_data(result: object, resource: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise CameraImageResponseError(f"Invalid response from {resource} service")

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        message = (
            first.get("message", "Unknown GraphQL error")
            if isinstance(first, dict)
            else "Unknown GraphQL error"
        )
        raise CameraImageResponseError(str(message))

    data = result.get("data")
    if not isinstance(data, dict):
        raise CameraImageResponseError(f"Invalid response from {resource} service")
    return data


def _optional_string(value: object, default: str) -> str:
    return value if isinstance(value, str) else default

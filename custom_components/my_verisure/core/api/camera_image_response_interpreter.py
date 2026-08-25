"""Pure interpretation of camera image retrieval responses."""

from __future__ import annotations

from typing import Any

from ..application.models.camera_images import CameraPhotoSet, CameraThumbnail


class CameraImageResponseError(ValueError):
    """Provider response cannot be interpreted under the image contract."""

    def __init__(self, safe_message: str) -> None:
        self.safe_message = safe_message
        super().__init__(safe_message)


def interpret_thumbnail_response(result: object) -> CameraThumbnail:
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
        signal_type=_required_string(response, "signalType"),
        device_alias=_required_string(response, "deviceAlias"),
        timestamp=_required_string(response, "timestamp"),
        image=_required_string(response, "image"),
    )


def _required_string(response: dict[str, Any], key: str) -> str:
    value = response.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CameraImageResponseError("Missing required thumbnail field")
    return value


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
            raise CameraImageResponseError("Invalid camera image")
        image_id = raw_image.get("id")
        image_data = raw_image.get("image")
        if (
            not isinstance(image_id, str)
            or not image_id.strip()
            or not isinstance(image_data, str)
            or not image_data.strip()
        ):
            raise CameraImageResponseError("Invalid camera image")
        images.append({"id": image_id, "image": image_data})

    return CameraPhotoSet(images=images)


def _require_data(result: object, resource: str) -> dict[str, Any]:
    if not isinstance(result, dict):
        raise CameraImageResponseError(f"Invalid response from {resource} service")

    if "errors" in result:
        raise CameraImageResponseError("Image service request failed")

    data = result.get("data")
    if not isinstance(data, dict):
        raise CameraImageResponseError(f"Invalid response from {resource} service")
    return data

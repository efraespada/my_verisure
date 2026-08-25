"""Pure interpretation of camera request GraphQL responses."""

from __future__ import annotations

from dataclasses import dataclass

from .camera_request_polling import (
    NO_RESPONSE_TO_REQUEST,
    PROCESSING_MESSAGE,
    REQUEST_ALREADY_EXISTS,
)


@dataclass(frozen=True)
class CameraRequestAccepted:
    """Accepted provider request with its polling reference."""

    reference_id: str


@dataclass(frozen=True)
class CameraStatus:
    """Interpreted provider status response."""

    result: str
    message: str


class CameraResponseError(ValueError):
    """Provider response cannot be interpreted under the camera contract."""

    _SAFE_MESSAGES = {
        "camera_response_invalid": "Invalid response from camera service",
        "camera_request_failed": "Camera request failed",
        "camera_response_empty": "Empty response from camera service",
        "camera_reference_missing": "No reference ID received from camera service",
        "camera_status_invalid": "Invalid response from camera status service",
        "camera_status_failed": "Failed to check images status",
    }

    def __init__(self, code: str) -> None:
        self.code = code
        self.safe_message = self._SAFE_MESSAGES.get(code, "Camera response failed")
        super().__init__(self.safe_message)


def interpret_request_response(result: object) -> CameraRequestAccepted:
    """Interpret the initial xSRequestImages mutation response."""
    if not isinstance(result, dict):
        raise CameraResponseError("camera_response_invalid")

    errors = result.get("errors")
    if "errors" in result:
        if not isinstance(errors, list) or len(errors) != 1:
            raise CameraResponseError("camera_request_failed")
        first = errors[0]
        provider_message = first.get("message") if isinstance(first, dict) else None
        if not isinstance(provider_message, str):
            raise CameraResponseError("camera_request_failed")
        if REQUEST_ALREADY_EXISTS in provider_message:
            raise CameraResponseError(REQUEST_ALREADY_EXISTS)
        raise CameraResponseError("camera_request_failed")

    data = result.get("data")
    response = data.get("xSRequestImages") if isinstance(data, dict) else None
    if not isinstance(response, dict) or not response:
        raise CameraResponseError("camera_response_empty")

    reference_id = response.get("referenceId")
    if not reference_id:
        raise CameraResponseError("camera_reference_missing")
    return CameraRequestAccepted(reference_id=str(reference_id))


def interpret_status_response(result: object) -> CameraStatus:
    """Interpret a status response using only bounded status codes."""
    if not isinstance(result, dict):
        raise CameraResponseError("camera_status_invalid")

    errors = result.get("errors")
    if "errors" in result:
        if not isinstance(errors, list) or len(errors) != 1:
            raise CameraResponseError("camera_status_failed")
        first = errors[0]
        provider_message = first.get("message") if isinstance(first, dict) else None
        if not isinstance(provider_message, str):
            raise CameraResponseError("camera_status_failed")
        if NO_RESPONSE_TO_REQUEST in provider_message:
            raise CameraResponseError(NO_RESPONSE_TO_REQUEST)
        raise CameraResponseError("camera_status_failed")

    data = result.get("data")
    response = data.get("xSRequestImagesStatus") if isinstance(data, dict) else None
    if not isinstance(response, dict) or not response:
        raise CameraResponseError("camera_status_invalid")

    status = response.get("res")
    if not status:
        raise CameraResponseError("camera_status_failed")
    provider_message = response.get("msg", "")
    message = PROCESSING_MESSAGE if PROCESSING_MESSAGE in str(provider_message) else "camera_status_complete"
    return CameraStatus(result=str(status), message=message)

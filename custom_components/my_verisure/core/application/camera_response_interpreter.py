"""Pure interpretation of camera request GraphQL responses."""

from __future__ import annotations

from dataclasses import dataclass


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


def interpret_request_response(result: object) -> CameraRequestAccepted:
    """Interpret the initial xSRequestImages mutation response."""
    if not isinstance(result, dict):
        raise CameraResponseError("Invalid response from camera service")

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        message = first.get("message", "Unknown GraphQL error") if isinstance(first, dict) else "Unknown GraphQL error"
        raise CameraResponseError(str(message))

    data = result.get("data")
    response = data.get("xSRequestImages") if isinstance(data, dict) else None
    if not isinstance(response, dict) or not response:
        raise CameraResponseError("Empty response from camera service")

    reference_id = response.get("referenceId")
    if not reference_id:
        raise CameraResponseError("No reference ID received from camera service")
    return CameraRequestAccepted(reference_id=str(reference_id))


def interpret_status_response(result: object) -> CameraStatus:
    """Interpret a status response while preserving provider messages."""
    if not isinstance(result, dict):
        raise CameraResponseError("Invalid response from camera status service")

    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        first = errors[0]
        message = first.get("message", "Unknown GraphQL error") if isinstance(first, dict) else "Unknown GraphQL error"
        raise CameraResponseError(str(message))

    data = result.get("data")
    response = data.get("xSRequestImagesStatus") if isinstance(data, dict) else None
    if not isinstance(response, dict) or not response:
        raise CameraResponseError("Invalid response from camera status service")

    status = response.get("res")
    if not status:
        raise CameraResponseError(
            f"Failed to check images status: {response.get('msg', 'Unknown error')}"
        )
    return CameraStatus(result=str(status), message=str(response.get("msg", "UNKNOWN")))

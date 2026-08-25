"""Contract tests for camera image response interpretation."""

import pytest

from custom_components.my_verisure.core.api.camera_image_response_interpreter import (
    CameraImageResponseError,
    interpret_photo_response,
    interpret_thumbnail_response,
)
from custom_components.my_verisure.core.application.models.camera_images import (
    CameraPhotoSet,
    CameraThumbnail,
)


def test_interprets_thumbnail_metadata_and_defaults() -> None:
    result = interpret_thumbnail_response(
        {
            "data": {
                "xSGetThumbnail": {
                    "idSignal": "signal-1",
                    "deviceAlias": "Front",
                    "signalType": "16",
                    "timestamp": "2026-08-25T10:00:00Z",
                    "image": "base64",
                }
            }
        },
    )

    assert result.id_signal == "signal-1"
    assert result.signal_type == "16"
    assert result.device_alias == "Front"
    assert result.timestamp == "2026-08-25T10:00:00Z"
    assert result.image == "base64"


def test_rejects_malformed_photo_entries() -> None:
    with pytest.raises(CameraImageResponseError, match="Invalid camera image"):
        interpret_photo_response(
            {
                "data": {
                    "xSGetPhotoImages": {
                        "devices": [{"images": [None]}]
                    }
                }
            }
        )


@pytest.mark.parametrize(
    "interpreter, payload, message",
    [
        (interpret_thumbnail_response, {"data": {}}, "Invalid response from thumbnail service"),
        (interpret_photo_response, {"data": {}}, "Invalid response from photo images service"),
        (
            interpret_thumbnail_response,
            {"errors": [{"message": "provider failed"}]},
            "Image service request failed",
        ),
    ],
)
def test_rejects_invalid_image_envelopes(interpreter, payload, message: str) -> None:
    with pytest.raises(CameraImageResponseError, match=message):
        if interpreter is interpret_thumbnail_response:
            interpreter(payload)
        else:
            interpreter(payload)


def test_thumbnail_requires_signal() -> None:
    with pytest.raises(CameraImageResponseError, match="No idSignal"):
        interpret_thumbnail_response(
            {"data": {"xSGetThumbnail": {"image": "base64"}}},
        )


    with pytest.raises(CameraImageResponseError, match="Missing required thumbnail field"):
        interpret_thumbnail_response(
            {
                "data": {
                    "xSGetThumbnail": {
                        "idSignal": "signal-1",
                        "deviceAlias": "Front",
                        "signalType": "16",
                        "timestamp": "2026-08-25T10:00:00Z",
                    }
                }
            },
        )


def test_photo_response_accepts_empty_device_collection() -> None:
    result = interpret_photo_response(
        {"data": {"xSGetPhotoImages": {"devices": []}}}
    )

    assert result.images == []

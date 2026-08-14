"""Contract tests for camera image response interpretation."""

import pytest

from custom_components.my_verisure.core.application.camera_image_response_interpreter import (
    CameraImageResponseError,
    interpret_photo_response,
    interpret_thumbnail_response,
)


def test_interprets_thumbnail_metadata_and_defaults() -> None:
    result = interpret_thumbnail_response(
        {
            "data": {
                "xSGetThumbnail": {
                    "idSignal": "signal-1",
                    "deviceAlias": "Front",
                    "image": "base64",
                }
            }
        },
        default_zone="YR01",
    )

    assert result.id_signal == "signal-1"
    assert result.signal_type == "16"
    assert result.device_alias == "Front"
    assert result.timestamp == ""
    assert result.image == "base64"


def test_interprets_first_photo_device_and_ignores_malformed_entries() -> None:
    result = interpret_photo_response(
        {
            "data": {
                "xSGetPhotoImages": {
                    "devices": [
                        {
                            "images": [
                                {"id": "0", "image": "photo-0"},
                                {"id": "1", "image": "photo-1"},
                                None,
                                {"id": 2, "image": "invalid-id"},
                            ]
                        }
                    ]
                }
            }
        }
    )

    assert result.images == [
        {"id": "0", "image": "photo-0"},
        {"id": "1", "image": "photo-1"},
    ]


@pytest.mark.parametrize(
    "interpreter, payload, message",
    [
        (interpret_thumbnail_response, {"data": {}}, "Invalid response from thumbnail service"),
        (interpret_photo_response, {"data": {}}, "Invalid response from photo images service"),
        (
            interpret_thumbnail_response,
            {"errors": [{"message": "provider failed"}]},
            "provider failed",
        ),
    ],
)
def test_rejects_invalid_image_envelopes(interpreter, payload, message: str) -> None:
    with pytest.raises(CameraImageResponseError, match=message):
        if interpreter is interpret_thumbnail_response:
            interpreter(payload, default_zone="YR01")
        else:
            interpreter(payload)


def test_thumbnail_requires_signal() -> None:
    with pytest.raises(CameraImageResponseError, match="No idSignal"):
        interpret_thumbnail_response(
            {"data": {"xSGetThumbnail": {"image": "base64"}}},
            default_zone="YR01",
        )


def test_photo_response_accepts_empty_device_collection() -> None:
    result = interpret_photo_response(
        {"data": {"xSGetPhotoImages": {"devices": []}}}
    )

    assert result.images == []

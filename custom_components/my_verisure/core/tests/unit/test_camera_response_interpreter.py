"""Tests for camera response interpretation."""

import pytest

from custom_components.my_verisure.core.api.camera_response_interpreter import (
    CameraResponseError,
    interpret_request_response,
    interpret_status_response,
)


def test_interprets_request_reference() -> None:
    result = interpret_request_response(
        {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref-1"}}}
    )

    assert result.reference_id == "ref-1"


@pytest.mark.parametrize(
    "payload, message",
    [
        ({}, "Empty response"),
        ({"data": {"xSRequestImages": {"res": "OK"}}}, "No reference ID"),
        ({"errors": [{"message": "provider failed"}]}, "Camera request failed"),
        ({"errors": [{"message": None}]}, "Camera request failed"),
    ],
)
def test_rejects_invalid_request_payload(payload: object, message: str) -> None:
    with pytest.raises(CameraResponseError, match=message):
        interpret_request_response(payload)


def test_interprets_processing_status() -> None:
    result = interpret_status_response(
        {
            "data": {
                "xSRequestImagesStatus": {
                    "res": "OK",
                    "msg": "alarm-manager.photo-request.processing",
                }
            }
        }
    )

    assert result.result == "OK"
    assert result.message.endswith("processing")



def test_rejects_malformed_status_error_message() -> None:
    with pytest.raises(CameraResponseError, match="Failed to check"):
        interpret_status_response({"errors": [{"message": None}]})


def test_rejects_invalid_status_payload() -> None:
    with pytest.raises(CameraResponseError, match="Invalid response"):
        interpret_status_response({"data": {}})

"""Fail-closed contracts for camera request DTOs."""

import pytest

from custom_components.my_verisure.core.api.models.dto.camera_request_image_dto import (
    CameraRequestImageDTO,
    CameraRequestImageResultDTO,
    CameraRequestImageStatusDTO,
)


def test_camera_request_dto_rejects_missing_success() -> None:
    with pytest.raises(ValueError, match="camera success required"):
        CameraRequestImageDTO.from_dict({})


def test_camera_status_dto_rejects_missing_success() -> None:
    with pytest.raises(ValueError, match="camera success required"):
        CameraRequestImageStatusDTO.from_dict({})


def test_camera_result_dto_rejects_missing_result_count() -> None:
    with pytest.raises(ValueError, match="camera successful_requests required"):
        CameraRequestImageResultDTO.from_dict({"success": True})

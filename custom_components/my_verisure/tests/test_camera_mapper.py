"""Contract tests for camera DTO adapters."""

from custom_components.my_verisure.core.api.mappers.camera_mapper import (
    request_image_from_dto,
    request_image_result_from_dto,
    request_image_result_to_dto,
    request_image_status_from_dto,
    request_image_status_to_dto,
    request_image_to_dto,
)
from custom_components.my_verisure.core.api.models.domain.camera_request_image import (
    CameraRequestImage,
    CameraRequestImageResult,
    CameraRequestImageStatus,
)
from custom_components.my_verisure.core.api.models.dto.camera_request_image_dto import (
    CameraRequestImageDTO,
    CameraRequestImageResultDTO,
    CameraRequestImageStatusDTO,
)


def test_request_mapping_round_trip() -> None:
    dto = CameraRequestImageDTO(True, "ref", "requested", None)
    value = request_image_from_dto(dto)
    assert value == CameraRequestImage(True, "ref", "requested", None)
    assert request_image_to_dto(value) == dto


def test_status_mapping_round_trip() -> None:
    dto = CameraRequestImageStatusDTO(True, "ready", 2, "ok", "installation", None)
    value = request_image_status_from_dto(dto)
    assert value == CameraRequestImageStatus(True, "ready", 2, "ok", "installation", None)
    assert request_image_status_to_dto(value) == dto


def test_result_mapping_round_trip() -> None:
    dto = CameraRequestImageResultDTO(True, 2, "ref")
    value = request_image_result_from_dto(dto)
    assert value == CameraRequestImageResult(True, 2, "ref")
    assert request_image_result_to_dto(value) == dto

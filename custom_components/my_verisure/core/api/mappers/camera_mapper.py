"""Mappings between camera image DTOs and domain values."""

from ..models.domain.camera_request_image import (
    CameraRequestImage,
    CameraRequestImageResult,
    CameraRequestImageStatus,
)
from ..models.dto.camera_request_image_dto import (
    CameraRequestImageDTO,
    CameraRequestImageResultDTO,
    CameraRequestImageStatusDTO,
)


def request_image_from_dto(dto: CameraRequestImageDTO) -> CameraRequestImage:
    return CameraRequestImage(dto.success, dto.reference_id, dto.message, dto.error)


def request_image_to_dto(value: CameraRequestImage) -> CameraRequestImageDTO:
    return CameraRequestImageDTO(value.success, value.reference_id, value.message, value.error)


def request_image_status_from_dto(dto: CameraRequestImageStatusDTO) -> CameraRequestImageStatus:
    return CameraRequestImageStatus(
        dto.success,
        dto.status,
        dto.counter,
        dto.message,
        dto.installation_id,
        dto.error,
    )


def request_image_status_to_dto(value: CameraRequestImageStatus) -> CameraRequestImageStatusDTO:
    return CameraRequestImageStatusDTO(
        value.success,
        value.status,
        value.counter,
        value.message,
        value.installation_id,
        value.error,
    )


def request_image_result_from_dto(dto: CameraRequestImageResultDTO) -> CameraRequestImageResult:
    return CameraRequestImageResult(dto.success, dto.successful_requests, dto.reference_id)


def request_image_result_to_dto(value: CameraRequestImageResult) -> CameraRequestImageResultDTO:
    return CameraRequestImageResultDTO(
        value.success,
        value.successful_requests,
        value.reference_id,
    )

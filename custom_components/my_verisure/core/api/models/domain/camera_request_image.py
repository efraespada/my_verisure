"""Camera Request Image domain models for My Verisure API."""

from dataclasses import dataclass
from typing import Optional

from ..dto.camera_request_image_dto import CameraRequestImageResultDTO, CameraRequestImageDTO, CameraRequestImageStatusDTO


@dataclass
class CameraRequestImage:
    """Domain model for camera image request."""
    
    success: bool
    reference_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: CameraRequestImageDTO) -> "CameraRequestImage":
        """Create domain model from DTO."""
        return cls(
            success=dto.success,
            reference_id=dto.reference_id,
            message=dto.message,
            error=dto.error,
        )

    def to_dto(self) -> CameraRequestImageDTO:
        """Convert domain model to DTO."""
        return CameraRequestImageDTO(
            success=self.success,
            reference_id=self.reference_id,
            message=self.message,
            error=self.error,
        )


@dataclass
class CameraRequestImageStatus:
    """Domain model for camera status check."""
    
    success: bool
    status: Optional[str] = None
    counter: Optional[int] = None
    message: Optional[str] = None
    installation_id: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: CameraRequestImageStatusDTO) -> "CameraRequestImageStatus":
        """Create domain model from DTO."""
        return cls(
            success=dto.success,
            status=dto.status,
            counter=dto.counter,
            message=dto.message,
            installation_id=dto.installation_id,
            error=dto.error,
        )

    def to_dto(self) -> CameraRequestImageStatusDTO:
        """Convert domain model to DTO."""
        return CameraRequestImageStatusDTO(
            success=self.success,
            status=self.status,
            counter=self.counter,
            message=self.message,
            installation_id=self.installation_id,
            error=self.error,
        )


@dataclass
class CameraRequestImageResult:
    """Domain model for camera image result."""
    
    success: bool
    successful_requests: int
    reference_id: Optional[str] = None

    @classmethod
    def from_dto(cls, dto: CameraRequestImageResultDTO) -> "CameraRequestImageResult":
        """Create domain model from DTO."""
        return cls(
            success=dto.success,
            successful_requests=dto.successful_requests,
            reference_id=dto.reference_id,
        )

    def to_dto(self) -> CameraRequestImageResultDTO:
        """Convert domain model to DTO."""
        return CameraRequestImageResultDTO(
            success=self.success,
            successful_requests=self.successful_requests,
            reference_id=self.reference_id,
        )

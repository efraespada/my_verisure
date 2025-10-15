"""Refresh camera images use case interface."""

from abc import ABC, abstractmethod

from ...api.models.domain.camera_request_image import CameraRequestImageResult


class RefreshCameraImagesUseCase(ABC):
    """Interface for refresh camera images use case."""

    @abstractmethod
    async def refresh_camera_images(
        self,
        installation_id: str,
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRequestImageResult:
        """Refresh images from cameras."""
        pass

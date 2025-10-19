"""Create dummy camera images use case interface."""

from abc import ABC, abstractmethod

from ...api.models.domain.camera_refresh import CameraRefresh


class CreateDummyCameraImagesUseCase(ABC):
    """Interface for create dummy camera images use case."""

    @abstractmethod
    async def create_dummy_camera_images(
        self,
        installation_id: str,
    ) -> CameraRefresh:
        """Create dummy images for cameras."""
        pass

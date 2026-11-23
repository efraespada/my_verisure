"""Create dummy camera images use case interface."""

from abc import ABC, abstractmethod

from ...application.models.camera_refresh import CameraRefresh


class CreateDummyCameraImagesUseCase(ABC):
    """Interface for create dummy camera images use case."""

    @abstractmethod
    async def create_dummy_camera_images(
        self,
        installation_id: str,
        *,
        camera_identifiers: tuple[str, ...] | None = None,
    ) -> CameraRefresh:
        """Ensure local images; discover cameras only when none were supplied."""
        pass

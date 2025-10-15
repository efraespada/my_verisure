"""Refresh camera images use case implementation."""

import logging
from typing import List

from ...api.models.domain.camera_request_image import CameraRequestImageResult
from ...repositories.interfaces.camera_repository import CameraRepository
from ...repositories.interfaces.installation_repository import InstallationRepository
from ..interfaces.refresh_camera_images_use_case import RefreshCameraImagesUseCase


_LOGGER = logging.getLogger(__name__)


class RefreshCameraImagesUseCaseImpl(RefreshCameraImagesUseCase):
    """Implementation of refresh camera images use case."""

    def __init__(
        self,
        camera_repository: CameraRepository,
        installation_repository: InstallationRepository,
    ) -> None:
        """Initialize the refresh camera images use case."""
        self.camera_repository = camera_repository
        self.installation_repository = installation_repository

    async def refresh_camera_images(
        self,
        installation_id: str,
        devices: List[int],
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRequestImageResult:
        """Refresh images from cameras."""
        try:
            _LOGGER.info(
                "Refreshing camera images for installation %s, devices %s",
                installation_id,
                devices,
            )

            # Get installation services to get panel and capabilities
            services_data = await self.installation_repository.get_installation_services(
                installation_id
            )
            panel = services_data.installation.panel or "SDVFAST"
            capabilities = services_data.installation.capabilities or "default_capabilities"

            _LOGGER.info(
                "Using panel %s and capabilities %s for camera refresh",
                panel,
                capabilities,
            )

            # Request images from cameras
            result = await self.camera_repository.request_image(
                installation_id=installation_id,
                panel=panel,
                devices=devices,
                max_attempts=max_attempts,
                check_interval=check_interval,
            )

            _LOGGER.info(
                "Camera images refresh completed. Success: %s, Status: %s, Attempts: %s",
                result.success,
                result.status,
                result.attempts,
            )

            return result

        except Exception as e:
            _LOGGER.error("Failed to refresh camera images: %s", e)
            # Return error result
            return CameraRequestImageResult(
                success=False,
                error=str(e),
                message=f"Camera images refresh failed: {str(e)}",
            )

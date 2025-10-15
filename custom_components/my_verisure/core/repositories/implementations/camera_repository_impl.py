"""Camera repository implementation."""

import logging
from typing import List

from ...api.camera_client import CameraClient
from ...api.models.domain.camera_request_image import CameraRequestImageResult
from ...api.models.dto.camera_request_image_dto import CameraRequestImageResultDTO
from ..interfaces.camera_repository import CameraRepository


_LOGGER = logging.getLogger(__name__)


class CameraRepositoryImpl(CameraRepository):
    """Implementation of camera repository."""

    def __init__(self, client: CameraClient) -> None:
        """Initialize the camera repository."""
        self.client = client

    async def request_image(
        self,
        installation_id: str,
        panel: str,
        devices: List[int],
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRequestImageResult:
        """Request images from cameras."""
        try:
            _LOGGER.info(
                "Requesting images for installation %s, panel %s, devices %s",
                installation_id,
                panel,
                devices,
            )

            # Call the camera client
            result = await self.client.request_image(
                installation_id=installation_id,
                panel=panel,
                devices=devices,
                max_attempts=max_attempts,
                check_interval=check_interval,
            )

            # Convert to DTO and then to domain model
            dto = CameraRequestImageResultDTO.from_dict(result)
            domain_model = CameraRequestImageResult.from_dto(dto)

            _LOGGER.info(
                "Camera request completed. Success: %s, Status: %s, Attempts: %s",
                domain_model.success,
                domain_model.status,
                domain_model.attempts,
            )

            return domain_model

        except Exception as e:
            _LOGGER.error("Failed to request camera images: %s", e)
            # Return error result
            return CameraRequestImageResult(
                success=False,
                error=str(e),
                message=f"Camera request failed: {str(e)}",
            )

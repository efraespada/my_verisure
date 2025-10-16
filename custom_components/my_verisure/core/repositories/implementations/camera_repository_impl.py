"""Camera repository implementation."""

import logging
from typing import Any, Dict, List

from ...api.camera_client import CameraClient
from ...api.models.domain.camera_request_image import CameraRequestImageResult
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
        capabilities: str,
    ) -> CameraRequestImageResult:
        """Request images from cameras."""
        try:
            # Call the camera client
            result = await self.client.request_image(
                installation_id=installation_id,
                panel=panel,
                devices=devices,
                capabilities=capabilities,
            )

            # Convert DTO to domain model
            domain_model = CameraRequestImageResult.from_dto(result)

            return domain_model

        except Exception as e:
            _LOGGER.error("❌ Failed to request camera images: %s", e)
            # Return error result
            return CameraRequestImageResult(
                success=False,
                successful_requests=0,
                reference_id=None
            )

    async def get_images(
        self,
        installation_id: str,
        panel: str,
        device: str,
        zone_id: str,
        capabilities: str,
    ) -> Dict[str, Any]:
        """Get images from a specific camera device."""
        try:
            # Call the camera client
            result = await self.client.get_images(
                installation_id=installation_id,
                panel=panel,
                device=device,
                zone_id=zone_id,
                capabilities=capabilities,
            )

            return result

        except Exception as e:
            _LOGGER.error("❌ Failed to get camera images: %s", e)
            # Return error result
            return {
                "success": False,
                "error": str(e),
                "message": f"Camera images retrieval failed: {str(e)}",
            }

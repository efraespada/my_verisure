"""Camera repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...api.models.domain.camera_request_image import CameraRequestImageResult


class CameraRepository(ABC):
    """Interface for camera repository."""

    @abstractmethod
    async def request_image(
        self,
        installation_id: str,
        panel: str,
        devices: List[int],
        capabilities: str,
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRequestImageResult:
        """Request images from cameras."""
        pass

    @abstractmethod
    async def get_images(
        self,
        installation_id: str,
        panel: str,
        device: str,
        capabilities: str,
    ) -> Dict[str, Any]:
        """Get images from a specific camera device."""
        pass

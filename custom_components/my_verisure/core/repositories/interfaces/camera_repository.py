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
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRequestImageResult:
        """Request images from cameras."""
        pass

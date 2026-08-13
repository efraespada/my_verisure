"""Application policy for refreshing camera images."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from ..api.models.domain.camera_refresh import CameraRefresh

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CameraRefreshPolicy:
    """Stable polling settings for a coordinator camera refresh."""

    max_attempts: int = 30
    check_interval: int = 4


class CameraRefreshExecutor(Protocol):
    """Port for the camera refresh use case."""

    async def refresh_camera_images(
        self,
        *,
        installation_id: str,
        max_attempts: int,
        check_interval: int,
    ) -> CameraRefresh:
        """Refresh camera images."""


class CoordinatorCameraRefresh:
    """Execute and report a camera refresh independently of Home Assistant."""

    def __init__(
        self,
        executor: CameraRefreshExecutor,
        policy: CameraRefreshPolicy | None = None,
    ) -> None:
        self._executor = executor
        self._policy = policy or CameraRefreshPolicy()

    async def run(self, installation_id: str) -> CameraRefresh:
        """Run the configured camera refresh and log its result."""
        _LOGGER.info("Refreshing camera images for installation %s", installation_id)
        result = await self._executor.refresh_camera_images(
            installation_id=installation_id,
            max_attempts=self._policy.max_attempts,
            check_interval=self._policy.check_interval,
        )
        _LOGGER.info(
            "Camera images refresh completed: %d cameras, %d ok, %d failed",
            result.total_cameras,
            result.successful_refreshes,
            result.failed_refreshes,
        )
        return result

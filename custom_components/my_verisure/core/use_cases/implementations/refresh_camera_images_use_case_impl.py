"""Refresh camera images use case implementation."""

import asyncio
import logging
import time
from typing import List

from ...api.models.domain.camera_refresh import CameraRefresh
from ...api.models.domain.camera_refresh_data import CameraRefreshData
from ...repositories.interfaces.camera_repository import CameraRepository
from ...repositories.interfaces.installation_repository import InstallationRepository
from ..interfaces.refresh_camera_images_use_case import RefreshCameraImagesUseCase
from datetime import datetime


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
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRefresh:
        """Refresh images from cameras."""
        start_time = time.time()
        try:
            _LOGGER.info(
                "📸 Refreshing camera images for installation %s",
                installation_id,
            )

            # Get installation services to get panel and capabilities
            installation_services = await self.installation_repository.get_installation_services(
                installation_id
            )
            panel = installation_services.installation.panel or "SDVFAST"
            capabilities = installation_services.installation.capabilities or "default_capabilities"
            devices = installation_services.installation.devices
            
            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices = [
                device for device in devices 
                if device.type in ["YR", "YP"] and device.remote_use
            ]
            
            if not camera_devices:
                _LOGGER.warning("⚠️ No active camera devices (YR/YP) found in installation %s", installation_id)
                return CameraRefresh(
                    refresh_data=[],
                    total_cameras=0,
                    successful_refreshes=0,
                    failed_refreshes=0,
                    timestamp=datetime.now().isoformat(),
                )
            
            refresh_data = []
            index = 0
            for camera_device in camera_devices:
                try:
                    result = await self.camera_repository.request_image(
                        installation_id=installation_id,
                        panel=panel,
                        devices=[int(camera_device.code)],
                        capabilities=capabilities,
                    )

                    formatted_code = f"{camera_device.type}{int(camera_device.code):02d}"
                    if (result.successful_requests > 0):
                        _LOGGER.info("⏳ Waiting 3 seconds before retrieving images from camera %s...", formatted_code)
                        await asyncio.sleep(3)

                        image_result = await self.camera_repository.get_images(
                            installation_id=installation_id,
                            panel=panel,
                            device=camera_device.type,
                            zone_id=formatted_code,
                            capabilities=capabilities,
                        )
                        
                        refresh_data.append(
                            CameraRefreshData(
                                timestamp=datetime.now().isoformat(),
                                num_images=image_result.get("images_saved", 0),
                                camera_identifier=formatted_code,
                            )
                        )

                        index = index + result.successful_requests

                        _LOGGER.info(
                            "✅ Camera images requests completed. Successful requests: %d/%d",
                            index,
                            len(camera_devices)
                        )

                except Exception as e:
                    _LOGGER.error(
                        "❌ Failed to retrieve images from camera %s: %s",
                        camera_device.name,
                        e,
                    )
                    
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=datetime.now().isoformat(),
                            num_images=0,
                            camera_identifier=formatted_code,
                        )
                    )

            _LOGGER.info(
                "🎉 Camera images retrieval completed for %d cameras",
                len(camera_devices),
            )
            
            # Calculate total execution time
            total_time = time.time() - start_time
            _LOGGER.info(
                "⏱️ Total execution time: %.2f seconds",
                total_time
            )
            
            # Return the original request result with additional images information
            return CameraRefresh(
                refresh_data=refresh_data,
                total_cameras=len(camera_devices),
                successful_refreshes=index,
                failed_refreshes=len(camera_devices) - index,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            # Calculate total execution time even in case of error
            total_time = time.time() - start_time
            _LOGGER.error("💥 Failed to refresh camera images: %s", e)
            _LOGGER.info(
                "⏱️ Total execution time (with error): %.2f seconds",
                total_time
            )
            # Return error result
            return CameraRefresh(
                refresh_data=[],
                total_cameras=0,
                successful_refreshes=0,
                failed_refreshes=0,
                timestamp=datetime.now().isoformat(),
            )

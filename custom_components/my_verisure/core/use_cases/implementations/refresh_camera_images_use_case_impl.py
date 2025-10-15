"""Refresh camera images use case implementation."""

import asyncio
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
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> CameraRequestImageResult:
        """Refresh images from cameras."""
        try:
            _LOGGER.info(
                "Refreshing camera images for installation %s",
                installation_id,
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

            # Get installation devices
            devices_data = await self.installation_repository.get_installation_devices(
                installation_id, panel
            )
            
            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices = [
                device for device in devices_data.devices 
                if device.type in ["YR", "YP"] and device.remote_use
            ]
            
            if not camera_devices:
                _LOGGER.warning("No active camera devices (YR/YP) found in installation %s", installation_id)
                return CameraRequestImageResult(
                    success=False,
                    message="No active camera devices found",
                )
            
            # Extract device IDs for camera request
            device_ids = [int(device.id) for device in camera_devices]
            
            _LOGGER.info(
                "Found %d active camera devices: %s",
                len(camera_devices),
                [f"{device.name} (ID: {device.id})" for device in camera_devices],
            )

            # Request images from cameras
            result = await self.camera_repository.request_image(
                installation_id=installation_id,
                panel=panel,
                devices=device_ids,
                capabilities=capabilities,
                max_attempts=max_attempts,
                check_interval=check_interval,
            )

            _LOGGER.info(
                "Camera images request completed. Success: %s, Status: %s, Attempts: %s",
                result.success,
                result.status,
                result.attempts,
            )

            # If the request was successful, wait 30 seconds and then get images from each camera
            if result.success:
                _LOGGER.info("Waiting 30 seconds before retrieving images from cameras...")
                await asyncio.sleep(30)

                _LOGGER.info("Starting to retrieve images from each camera...")
                
                # Get images from each camera device
                images_results = []
                for camera_device in camera_devices:
                    try:
                        _LOGGER.info(
                            "Retrieving images from camera %s (ID: %s, Device: %s)",
                            camera_device.name,
                            camera_device.id,
                            camera_device.type + camera_device.code,
                        )
                        
                        # Call get_images for each camera
                        image_result = await self.camera_repository.get_images(
                            installation_id=installation_id,
                            panel=panel,
                            device=camera_device.type + camera_device.code,  # Use type + code (e.g., "YR1", "YP2")
                            capabilities=capabilities,
                        )
                        
                        images_results.append({
                            "device": camera_device.name,
                            "device_code": camera_device.code,
                            "result": image_result,
                        })
                        
                        _LOGGER.info(
                            "Images retrieved for camera %s. Success: %s, Images saved: %s",
                            camera_device.name,
                            image_result.get("success", False),
                            image_result.get("images_saved", 0),
                        )
                        
                    except Exception as e:
                        _LOGGER.error(
                            "Failed to retrieve images from camera %s: %s",
                            camera_device.name,
                            e,
                        )
                        images_results.append({
                            "device": camera_device.name,
                            "device_code": camera_device.code,
                            "result": {
                                "success": False,
                                "error": str(e),
                                "message": f"Failed to retrieve images from {camera_device.name}",
                            },
                        })

                _LOGGER.info(
                    "Camera images retrieval completed for %d cameras",
                    len(images_results),
                )
                
                # Return the original request result with additional images information
                return CameraRequestImageResult(
                    success=result.success,
                    reference_id=result.reference_id,
                    status=result.status,
                    attempts=result.attempts,
                    message=f"Camera images refresh completed. {len(images_results)} cameras processed.",
                )
            else:
                _LOGGER.warning("Camera images request failed, skipping image retrieval")
                return result

            return result

        except Exception as e:
            _LOGGER.error("Failed to refresh camera images: %s", e)
            # Return error result
            return CameraRequestImageResult(
                success=False,
                error=str(e),
                message=f"Camera images refresh failed: {str(e)}",
            )

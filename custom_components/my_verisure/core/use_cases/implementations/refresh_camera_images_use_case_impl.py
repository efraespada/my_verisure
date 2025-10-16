"""Refresh camera images use case implementation."""

import asyncio
import logging
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

            # Get installation devices
            devices_data = await self.installation_repository.get_installation_devices(
                installation_id, panel
            )
            
            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices = [
                device for device in devices_data.devices 
                if device.type in ["YR", "YP"] and device.remote_use
            ]

            _LOGGER.info("Camera devices: %s", camera_devices)
            
            # Log detailed information for each camera device
            for i, device in enumerate(camera_devices, 1):
                _LOGGER.info("Camera %d details:", i)
                _LOGGER.info("  - ID: %s", device.id)
                _LOGGER.info("  - Name: %s", device.name)
                _LOGGER.info("  - Type: %s", device.type)
                _LOGGER.info("  - Code: %s", device.code)
                _LOGGER.info("  - Device ID: %s", device.type + device.code)
                _LOGGER.info("  - Remote Use: %s", device.remote_use)
                _LOGGER.info("  - Active: %s", device.is_active)
                if device.serial_number:
                    _LOGGER.info("  - Serial Number: %s", device.serial_number)
                if hasattr(device, 'config') and device.config:
                    _LOGGER.info("  - Config: %s", device.config)
                _LOGGER.info("  - Service ID: %s", device.id_service)
            
            if not camera_devices:
                _LOGGER.warning("No active camera devices (YR/YP) found in installation %s", installation_id)
                return CameraRefresh(
                    refresh_data=[],
                    total_cameras=0,
                    successful_refreshes=0,
                    failed_refreshes=0,
                    timestamp=datetime.now().isoformat(),
                )
            
            device_ids = [int(device.code) for device in camera_devices]
            
            _LOGGER.info(
                "Found %d active camera devices: %s",
                len(camera_devices),
                [f"{device.name} (ID: {device.id})" for device in camera_devices],
            )

            result = await self.camera_repository.request_image(
                installation_id=installation_id,
                panel=panel,
                devices=device_ids,  # Single device per request
                capabilities=capabilities,
            )

            _LOGGER.info(
                "Camera images requests completed. Successful requests: %d/%d",
                result.successful_requests,
                len(device_ids)
            )

            refresh_data = []

            # If we had any successful requests, wait 10 seconds and then get images from each camera
            _LOGGER.info("Waiting 10 seconds before retrieving images from cameras...")
            await asyncio.sleep(10)

            _LOGGER.info("Starting to retrieve images from each camera...")
            
            for camera_device in camera_devices:
                # Format device code with zero padding for single digits
                formatted_code = camera_device.type + f"{camera_device.code:02d}"
                
                try:
                    # Call get_images for each camera
                    image_result = await self.camera_repository.get_images(
                        installation_id=installation_id,
                        panel=panel,
                        device=camera_device.type,
                        zone_id=formatted_code,
                        capabilities=capabilities,
                    )
                    
                    _LOGGER.info(
                        "Retrieving images from camera %s (ID: %s, Device: %s)",
                        camera_device.name,
                        camera_device.id,
                        formatted_code,
                    )
                    
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=datetime.now().isoformat(),
                            num_images=image_result.get("images_saved", 0),
                            camera_identifier=formatted_code,
                        )
                    )
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
                    
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=datetime.now().isoformat(),
                            num_images=0,
                            camera_identifier=formatted_code,
                        )
                    )

            _LOGGER.info(
                "Camera images retrieval completed for %d cameras",
                len(camera_devices),
            )
            
            # Return the original request result with additional images information
            return CameraRefresh(
                refresh_data=refresh_data,
                total_cameras=len(camera_devices),
                successful_refreshes=len(refresh_data),
                failed_refreshes=len(camera_devices) - len(refresh_data),
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            _LOGGER.error("Failed to refresh camera images: %s", e)
            # Return error result
            return CameraRefresh(
                refresh_data=[],
                total_cameras=0,
                successful_refreshes=0,
                failed_refreshes=0,
                timestamp=datetime.now().isoformat(),
            )

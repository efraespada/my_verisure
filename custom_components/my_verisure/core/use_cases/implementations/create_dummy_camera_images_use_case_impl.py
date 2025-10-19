"""Create dummy camera images use case implementation."""

import logging
import os
from datetime import datetime
from PIL import Image

from ...api.models.domain.camera_refresh import CameraRefresh
from ...api.models.domain.camera_refresh_data import CameraRefreshData
from ...repositories.interfaces.installation_repository import InstallationRepository
from ...file_manager import get_file_manager
from ..interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase


_LOGGER = logging.getLogger(__name__)


class CreateDummyCameraImagesUseCaseImpl(CreateDummyCameraImagesUseCase):
    """Implementation of create dummy camera images use case."""

    def __init__(
        self,
        installation_repository: InstallationRepository,
    ) -> None:
        """Initialize the create dummy camera images use case."""
        self.installation_repository = installation_repository

    async def create_dummy_camera_images(
        self,
        installation_id: str,
    ) -> CameraRefresh:
        """Create dummy images for cameras."""
        try:
            _LOGGER.info(
                "🎭 Creating dummy camera images for installation %s",
                installation_id,
            )

            # Get installation services to get devices
            detailed_installation = await self.installation_repository.get_installation_services(
                installation_id
            )
            devices = detailed_installation.installation.devices
            
            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices = [
                device for device in devices 
                if device.type in ["YR", "YP"]
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
            successful_count = 0
            
            # Get the data directory path
            data_path = get_file_manager().get_data_directory()
            cameras_dir = os.path.join(data_path, "cameras")
            
            # Create cameras directory if it doesn't exist
            os.makedirs(cameras_dir, exist_ok=True)
            
            for camera_device in camera_devices:
                try:
                    formatted_code = f"{camera_device.type}{int(camera_device.code):02d}"
                    camera_dir = os.path.join(cameras_dir, formatted_code)
                    
                    # Check if camera already has images
                    if self._camera_has_existing_images(camera_dir):
                        _LOGGER.info(
                            "⏭️ Camera %s (%s) already has images, skipping dummy creation",
                            camera_device.name,
                            formatted_code
                        )
                        
                        refresh_data.append(
                            CameraRefreshData(
                                timestamp=datetime.now().isoformat(),
                                num_images=0,
                                camera_identifier=formatted_code,
                            )
                        )
                        continue
                    
                    # Create camera directory if it doesn't exist
                    os.makedirs(camera_dir, exist_ok=True)
                    
                    # Create timestamp directory (current date and time)
                    now = datetime.now()
                    timestamp_dir = now.strftime("%Y-%m-%d_%H-%M-%S")
                    timestamp_path = os.path.join(camera_dir, timestamp_dir)
                    os.makedirs(timestamp_path, exist_ok=True)
                    
                    # Create dummy black images
                    dummy_images_created = self._create_dummy_images(timestamp_path)
                    
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=datetime.now().isoformat(),
                            num_images=dummy_images_created,
                            camera_identifier=formatted_code,
                        )
                    )
                    
                    successful_count += 1
                    _LOGGER.info(
                        "✅ Created %d dummy images for camera %s (%s)",
                        dummy_images_created,
                        camera_device.name,
                        formatted_code
                    )

                except Exception as e:
                    _LOGGER.error(
                        "❌ Failed to create dummy images for camera %s: %s",
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
                "🎉 Dummy camera images creation completed for %d cameras",
                len(camera_devices),
            )
            
            return CameraRefresh(
                refresh_data=refresh_data,
                total_cameras=len(camera_devices),
                successful_refreshes=successful_count,
                failed_refreshes=len(camera_devices) - successful_count,
                timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            _LOGGER.error("💥 Failed to create dummy camera images: %s", e)
            return CameraRefresh(
                refresh_data=[],
                total_cameras=0,
                successful_refreshes=0,
                failed_refreshes=0,
                timestamp=datetime.now().isoformat(),
            )

    def _camera_has_existing_images(self, camera_dir: str) -> bool:
        """Check if camera already has existing images."""
        try:
            if not os.path.exists(camera_dir):
                return False
            
            # Look for any timestamp directories (YYYY-MM-DD_HH-MM-SS format)
            for item in os.listdir(camera_dir):
                item_path = os.path.join(camera_dir, item)
                if os.path.isdir(item_path):
                    # Check if this directory contains image files
                    for file in os.listdir(item_path):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            _LOGGER.debug("Found existing images in %s", item_path)
                            return True
            
            return False
            
        except Exception as e:
            _LOGGER.error("Error checking existing images for camera %s: %s", camera_dir, e)
            return False

    def _create_dummy_images(self, directory_path: str) -> int:
        """Create dummy black images in the specified directory."""
        try:
            # Create a black image (1920x1080 pixels)
            black_image = Image.new('RGB', (1920, 1080), color='black')
            
            # Create the required dummy images
            dummy_files = ['1.jpg', '2.jpg', '3.jpg', 'thumbnail.jpg']
            images_created = 0
            
            for filename in dummy_files:
                file_path = os.path.join(directory_path, filename)
                black_image.save(file_path, 'JPEG', quality=85)
                images_created += 1
                _LOGGER.debug("Created dummy image: %s", file_path)
            
            return images_created
            
        except Exception as e:
            _LOGGER.error("Failed to create dummy images in %s: %s", directory_path, e)
            return 0

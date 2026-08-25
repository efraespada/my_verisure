"""Create dummy camera images use case implementation."""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
from datetime import datetime
from PIL import Image

from ...application.models.camera_refresh import CameraRefresh
from ...application.models.camera_refresh_data import CameraRefreshData
from ...repositories.interfaces.installation_repository import InstallationRepository
from ...file_manager import FileManager
from ...application.camera_devices import camera_devices, camera_identifier
from ...application.exceptions import MyVerisureError
from ..interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase


_LOGGER = logging.getLogger(__name__)


class CreateDummyCameraImagesUseCaseImpl(CreateDummyCameraImagesUseCase):
    """Implementation of create dummy camera images use case."""

    def __init__(
        self,
        installation_repository: InstallationRepository,
        file_manager: FileManager,
    ) -> None:
        """Initialize the create dummy camera images use case."""
        self.installation_repository = installation_repository
        self.file_manager = file_manager

    async def create_dummy_camera_images(
        self,
        installation_id: str,
    ) -> CameraRefresh:
        """Create dummy images for cameras."""
        try:
            _LOGGER.info("🎭 Creating dummy camera images")

            # Get installation services to get devices
            detailed_installation = await self.installation_repository.get_installation_services(
                installation_id
            )
            devices = detailed_installation.installation.devices
            
            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices_list = camera_devices(devices)
            
            if not camera_devices_list:
                _LOGGER.warning("⚠️ No active camera devices (YR/YP) found")
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
            data_path = self.file_manager.get_data_directory()
            cameras_dir = os.path.join(data_path, "cameras")

            await asyncio.to_thread(
                lambda: os.makedirs(cameras_dir, exist_ok=True)
            )

            for camera_device in camera_devices_list:
                staging_path: str | None = None
                try:
                    formatted_code = camera_identifier(camera_device)
                    camera_dir = os.path.join(cameras_dir, formatted_code)

                    if await asyncio.to_thread(
                        self._camera_has_existing_images, camera_dir
                    ):
                        _LOGGER.info(
                            "⏭️ Camera already has images, skipping dummy creation",
                        )
                        
                        refresh_data.append(
                            CameraRefreshData(
                                timestamp=datetime.now().isoformat(),
                                num_images=0,
                                camera_identifier=formatted_code,
                            )
                        )
                        continue
                    
                    now = datetime.now()
                    timestamp_dir = now.strftime("%Y-%m-%d_%H-%M-%S")
                    timestamp_path = os.path.join(camera_dir, timestamp_dir)
                    staging_path = f"{timestamp_path}.staging"
                    await asyncio.to_thread(
                        self._sync_prepare_camera_dummy_dirs,
                        camera_dir,
                        staging_path,
                    )

                    dummy_images_created = await asyncio.to_thread(
                        self._create_dummy_images, staging_path
                    )
                    if not isinstance(dummy_images_created, int) or dummy_images_created <= 0:
                        raise MyVerisureError("Dummy camera image creation failed")
                    await asyncio.to_thread(os.replace, staging_path, timestamp_path)
                    
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=datetime.now().isoformat(),
                            num_images=dummy_images_created,
                            camera_identifier=formatted_code,
                        )
                    )
                    
                    successful_count += 1
                    _LOGGER.info(
                        "✅ Created %d dummy images for camera",
                        dummy_images_created,
                    )

                except asyncio.CancelledError:
                    if staging_path is not None:
                        try:
                            cleaned = await asyncio.to_thread(
                                self._sync_cleanup_staging_dir, staging_path
                            )
                        except Exception:
                            cleaned = False
                        if not cleaned:
                            _LOGGER.error(
                                "Dummy camera staging cleanup could not be confirmed"
                            )
                    raise
                except MyVerisureError:
                    if staging_path is not None:
                        cleaned = await asyncio.to_thread(
                            self._sync_cleanup_staging_dir, staging_path
                        )
                        if not cleaned:
                            raise MyVerisureError(
                                "Dummy camera staging cleanup failed"
                            ) from None
                    raise
                except Exception:
                    if staging_path is not None:
                        cleaned = await asyncio.to_thread(
                            self._sync_cleanup_staging_dir, staging_path
                        )
                        if not cleaned:
                            raise MyVerisureError(
                                "Dummy camera staging cleanup failed"
                            ) from None
                    _LOGGER.error("❌ Failed to create dummy images")
                    raise MyVerisureError(
                        "Dummy camera image creation failed"
                    ) from None

            _LOGGER.info(
                "🎉 Dummy camera images creation completed for %d cameras",
                len(camera_devices_list),
            )
            
            return CameraRefresh(
                refresh_data=refresh_data,
                total_cameras=len(camera_devices_list),
                successful_refreshes=successful_count,
                failed_refreshes=len(camera_devices_list) - successful_count,
                timestamp=datetime.now().isoformat(),
            )

        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("💥 Failed to create dummy camera images")
            raise MyVerisureError("Dummy camera image creation failed") from None

    @staticmethod
    def _sync_prepare_camera_dummy_dirs(camera_dir: str, timestamp_path: str) -> None:
        """Create camera and timestamp directories (blocking I/O)."""
        os.makedirs(camera_dir, exist_ok=True)
        os.makedirs(timestamp_path, exist_ok=True)

    @staticmethod
    def _sync_cleanup_staging_dir(staging_path: str) -> bool:
        """Remove an unpublished staging directory and verify it is gone."""
        shutil.rmtree(staging_path, ignore_errors=True)
        return not os.path.exists(staging_path)

    def _camera_has_existing_images(self, camera_dir: str) -> bool:
        """Check if camera already has existing images."""
        try:
            if not os.path.exists(camera_dir):
                return False
            
            # Look for any timestamp directories (YYYY-MM-DD_HH-MM-SS format)
            for item in os.listdir(camera_dir):
                item_path = os.path.join(camera_dir, item)
                if os.path.isdir(item_path):
                    marker_path = os.path.join(item_path, ".complete")
                    try:
                        with open(marker_path, "rb") as marker_file:
                            if marker_file.read() != b"complete":
                                continue
                    except OSError:
                        continue
                    # Check if this directory contains image files
                    for file in os.listdir(item_path):
                        if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            _LOGGER.debug("Found existing images")
                            return True
            
            return False
            
        except Exception:
            _LOGGER.error("Error checking existing camera images")
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
                temporary_path = f"{file_path}.tmp"
                try:
                    black_image.save(temporary_path, "JPEG", quality=85)
                    os.replace(temporary_path, file_path)
                finally:
                    try:
                        os.unlink(temporary_path)
                    except FileNotFoundError:
                        pass
                images_created += 1
                _LOGGER.debug("Created dummy image")
            
            marker_path = os.path.join(directory_path, ".complete")
            temporary_marker = f"{marker_path}.tmp"
            with open(temporary_marker, "wb") as marker:
                marker.write(b"complete")
                marker.flush()
                os.fsync(marker.fileno())
            os.replace(temporary_marker, marker_path)
            return images_created

        except Exception:
            shutil.rmtree(directory_path, ignore_errors=True)
            if os.path.exists(directory_path):
                _LOGGER.error("Failed to clean dummy image staging directory")
            _LOGGER.error("Failed to create dummy image files")
            return 0

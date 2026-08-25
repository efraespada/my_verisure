"""Camera commands for My Verisure CLI."""

import logging
from typing import Optional

from .base import BaseCommand
from ..utils.display import print_header, print_error, print_info, print_success

_LOGGER = logging.getLogger(__name__)


class CameraCommand(BaseCommand):
    """Camera command handler."""

    def __init__(self, session_manager=None, composition_root=None):
        """Initialize the camera command with the CLI composition root."""
        super().__init__(session_manager, composition_root)

    async def execute(
        self,
        action: str,
        installation_id: Optional[str] = None,
        interactive: bool = True,
    ) -> bool:
        """Execute camera command."""
        try:
            if not await self.setup(interactive):
                return False

            if action == "info":
                return await self._show_cameras_info(installation_id, interactive)
            elif action == "refresh-images":
                return await self._refresh_camera_images(installation_id, interactive)
            elif action == "create-dummies":
                return await self._create_dummy_camera_images(installation_id, interactive)
            else:
                print_error(f"Unknown camera action: {action}")
                return False

        except Exception:
            _LOGGER.error("Camera command failed")
            print_error("Camera command failed")
            return False

    async def _show_cameras_info(
        self, installation_id: Optional[str], interactive: bool
    ) -> bool:
        """Show camera devices information."""
        try:
            print_header("CAMERA DEVICES INFORMATION")

            # Get installation ID using BaseCommand method
            installation_id = await self.select_installation_if_needed(installation_id)
            if not installation_id:
                print_error("No installation selected")
                return False

            print_info("Getting camera devices for the selected installation")
        
            # Get installation devices
            devices = (await self.get_installation_devices_use_case.get_installation_devices(
                installation_id
            )).devices

            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices = [
                device
                for device in devices
                if device.type in ["YR", "YP"]
            ]

            if not camera_devices:
                print_info("No active camera devices (YR/YP) found in this installation")
                return True

            print_success(f"Found {len(camera_devices)} active camera devices:")
            print()

            for i, device in enumerate(camera_devices, 1):
                print_info(f"Camera {i}:")
                print(f"  Name: Camera {i}")
                print(f"  Type: {device.type}")
                print("  Code: [REDACTED]")
                print("  Device ID: [REDACTED]")
                print(f"  Remote Use: {device.remote_use}")
                print(f"  Active: {device.is_active}")
                if device.serial_number:
                    print("  Serial Number: [REDACTED]")
                print()

            return True

        except Exception:
            _LOGGER.error("Camera device lookup failed")
            print_error("Failed to get camera devices info")
            return False

    async def _refresh_camera_images(
        self, installation_id: Optional[str], interactive: bool
    ) -> bool:
        """Refresh camera images."""
        try:
            print_header("REFRESH CAMERA IMAGES")

            # Get installation ID using BaseCommand method
            installation_id = await self.select_installation_if_needed(installation_id)
            if not installation_id:
                print_error("No installation selected")
                return False

            print_info("Refreshing camera images for the selected installation")

            # Execute the refresh camera images use case
            result = await self.refresh_camera_images_use_case.refresh_camera_images(
                installation_id=installation_id,
                max_attempts=30,
                check_interval=4,
            )

            # Display results using the new CameraRefresh structure
            print_success("Camera images refresh completed!")
            print_info(f"Total cameras: {result.total_cameras}")
            print_info(f"Successful refreshes: {result.successful_refreshes}")
            print_info(f"Failed refreshes: {result.failed_refreshes}")
            print()

            if result.refresh_data:
                print_info("Camera refresh details:")
                for i, camera_data in enumerate(result.refresh_data, 1):
                    num_images = camera_data.num_images
                    timestamp = camera_data.timestamp
                    
                    if num_images > 0:
                        print_success(
                            f"  Camera {i}: {num_images} images saved at {timestamp}"
                        )
                    else:
                        print_error(
                            f"  Camera {i}: No images saved at {timestamp}"
                        )
            else:
                print_info("No camera refresh data available")

            # Show summary
            if result.successful_refreshes > 0:
                print_success(f"✓ Successfully refreshed {result.successful_refreshes} cameras")
            if result.failed_refreshes > 0:
                print_error(f"✗ Failed to refresh {result.failed_refreshes} cameras")

            return True

        except Exception:
            _LOGGER.error("Camera image refresh failed")
            print_error("Failed to refresh camera images")
            return False

    async def _create_dummy_camera_images(
        self, installation_id: Optional[str], interactive: bool
    ) -> bool:
        """Create dummy camera images."""
        try:
            print_header("CREATE DUMMY CAMERA IMAGES")

            # Get installation ID using BaseCommand method
            installation_id = await self.select_installation_if_needed(installation_id)
            if not installation_id:
                print_error("No installation selected")
                return False

            print_info("Creating dummy camera images for the selected installation")

            # Execute the create dummy camera images use case
            result = await self.create_dummy_camera_images_use_case.create_dummy_camera_images(
                installation_id=installation_id,
            )

            # Display results using the CameraRefresh structure
            print_success("Dummy camera images creation completed!")
            print_info(f"Total cameras: {result.total_cameras}")
            print_info(f"Successful creations: {result.successful_refreshes}")
            print_info(f"Failed creations: {result.failed_refreshes}")
            print()

            if result.refresh_data:
                print_info("Camera dummy creation details:")
                for i, camera_data in enumerate(result.refresh_data, 1):
                    num_images = camera_data.num_images
                    timestamp = camera_data.timestamp
                    
                    if num_images > 0:
                        print_success(
                            f"  Camera {i}: {num_images} dummy images created at {timestamp}"
                        )
                    else:
                        print_error(
                            f"  Camera {i}: No dummy images created at {timestamp}"
                        )
            else:
                print_info("No camera dummy creation data available")

            # Show summary
            if result.successful_refreshes > 0:
                print_success(f"✓ Successfully created dummy images for {result.successful_refreshes} cameras")
            if result.failed_refreshes > 0:
                print_error(f"✗ Failed to create dummy images for {result.failed_refreshes} cameras")

            return True

        except Exception:
            _LOGGER.error("Dummy camera image creation failed")
            print_error("Failed to create dummy camera images")
            return False

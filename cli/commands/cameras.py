"""Camera commands for My Verisure CLI."""

import asyncio
import logging
from typing import Optional

from .base import BaseCommand
from ..utils.display import print_header, print_error, print_info, print_success

_LOGGER = logging.getLogger(__name__)


class CameraCommand(BaseCommand):
    """Camera command handler."""

    def __init__(self):
        """Initialize the camera command."""
        super().__init__()

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
            else:
                print_error(f"Unknown camera action: {action}")
                return False

        except Exception as e:
            _LOGGER.error("Failed to execute camera command: %s", e)
            print_error(f"Camera command failed: {e}")
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

            print_info(f"Getting camera devices for installation: {installation_id}")

            # Get installation services to get panel
            services_data = await self.installation_use_case.get_installation_services(
                installation_id
            )
            panel = services_data.installation.panel or "SDVFAST"

            # Get installation devices
            devices_data = await self.get_installation_devices_use_case.get_installation_devices(
                installation_id, panel
            )

            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices = [
                device
                for device in devices_data.devices
                if device.type in ["YR", "YP"] and device.remote_use
            ]

            if not camera_devices:
                print_info("No active camera devices (YR/YP) found in this installation")
                return True

            print_success(f"Found {len(camera_devices)} active camera devices:")
            print()

            for i, device in enumerate(camera_devices, 1):
                print_info(f"Camera {i}:")
                print(f"  Name: {device.name}")
                print(f"  Type: {device.type}")
                print(f"  Code: {device.code}")
                print(f"  Device ID: {device.type + device.code}")
                print(f"  Remote Use: {device.remote_use}")
                print(f"  Active: {device.is_active}")
                if device.serial_number:
                    print(f"  Serial Number: {device.serial_number}")
                print()

            return True

        except Exception as e:
            _LOGGER.error("Failed to show camera devices info: %s", e)
            print_error(f"Failed to get camera devices info: {e}")
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

            print_info(f"Refreshing camera images for installation: {installation_id}")

            # Execute the refresh camera images use case
            result = await self.refresh_camera_images_use_case.refresh_camera_images(
                installation_id=installation_id,
                max_attempts=30,
                check_interval=4,
            )

            if result.success:
                print_success("Camera images refresh completed successfully!")
                print_info(f"Status: {result.status}")
                print_info(f"Attempts: {result.attempts}")
                if hasattr(result, 'images_results') and result.images_results:
                    print_info(f"Processed {len(result.images_results)} cameras:")
                    for camera_result in result.images_results:
                        device_name = camera_result.get("device", "Unknown")
                        device_code = camera_result.get("device_code", "Unknown")
                        result_data = camera_result.get("result", {})
                        
                        if result_data.get("success", False):
                            images_saved = result_data.get("images_saved", 0)
                            print_success(f"  ✓ {device_name} ({device_code}): {images_saved} images saved")
                        else:
                            error_msg = result_data.get("message", "Unknown error")
                            print_error(f"  ✗ {device_name} ({device_code}): {error_msg}")
            else:
                print_error(f"Camera images refresh failed: {result.message}")
                return False

            return True

        except Exception as e:
            _LOGGER.error("Failed to refresh camera images: %s", e)
            print_error(f"Failed to refresh camera images: {e}")
            return False

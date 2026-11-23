"""Refresh camera images use case implementation."""

import asyncio
from collections.abc import Callable
import logging
import time

from ...application.models.camera_refresh import CameraRefresh
from ...application.models.camera_refresh_data import CameraRefreshData
from ...application.camera_devices import (
    camera_devices as select_camera_devices,
    camera_identifier as camera_identifier_for_device,
)
from ...application.exceptions import MyVerisureError
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
        self._photo_committed_callback: Callable[[str, int, str | None], None] | None = None

    def set_photo_committed_callback(
        self, callback: Callable[[str, int, str | None], None] | None,
    ) -> None:
        """Observe saved captures without exposing HA APIs to the application."""
        self._photo_committed_callback = callback

    async def refresh_camera_images(
        self,
        installation_id: str,
        max_attempts: int = 30,
        check_interval: int = 20,
        camera_identifier: str | None = None,
    ) -> CameraRefresh:
        """Refresh images from cameras."""
        start_time = time.time()
        try:
            _LOGGER.info("📸 Refreshing camera images")

            # Get installation services to get panel and capabilities
            detailed_installation = await self.installation_repository.get_installation_services(
                installation_id
            )
            panel = detailed_installation.installation.panel
            capabilities = detailed_installation.installation.capabilities
            if not panel or not capabilities:
                raise MyVerisureError("Installation context unavailable")
            devices = detailed_installation.installation.devices
            
            # Filter devices to get only cameras (type "YR" or "YP")
            camera_devices_list = select_camera_devices(devices)
            if camera_identifier is not None:
                camera_devices_list = [
                    device for device in camera_devices_list
                    if camera_identifier == camera_identifier_for_device(device)
                ]
                if not camera_devices_list:
                    raise MyVerisureError("Selected camera unavailable")
            
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
            successful_refreshes = 0
            for camera_device in camera_devices_list:
                formatted_code = f"{camera_device.type}{int(camera_device.code):02d}"
                try:
                    result = await self.camera_repository.request_image(
                        installation_id=installation_id,
                        panel=panel,
                        devices=[int(camera_device.code)],
                        capabilities=capabilities,
                        max_attempts=max_attempts,
                        check_interval=check_interval,
                    )

                    formatted_code = camera_identifier_for_device(camera_device)
                    if (result.successful_requests > 0):
                        _LOGGER.info("⏳ Waiting before retrieving images")
                        signal_id = getattr(result, "signal_id", None)
                        if not isinstance(signal_id, str):
                            signal_id = None
                        if signal_id is None:
                            await asyncio.sleep(3)

                        image_result = await self.camera_repository.get_images(
                            installation_id=installation_id,
                            panel=panel,
                            device=camera_device.type,
                            zone_id=formatted_code,
                            capabilities=capabilities,
                            **({"signal_id": signal_id} if signal_id is not None else {}),
                        )
                        
                        persisted_successfully = image_result.get("success") is True
                        refresh_data.append(
                            CameraRefreshData(
                                timestamp=datetime.now().isoformat(),
                                num_images=image_result.get("images_saved", 0),
                                camera_identifier=formatted_code,
                            )
                        )

                        if persisted_successfully:
                            successful_refreshes += 1
                            _LOGGER.info("✅ Camera images persisted successfully")
                            image_count = image_result.get("images_saved", 0)
                            committed_signal = image_result.get("signal_id", signal_id)
                            if not isinstance(committed_signal, str) or not committed_signal.isdigit() or len(committed_signal) > 128:
                                committed_signal = None
                            if self._photo_committed_callback is not None and type(image_count) is int and 1 <= image_count <= 8:
                                try:
                                    self._photo_committed_callback(formatted_code, image_count, committed_signal)
                                except Exception:
                                    _LOGGER.warning("Photo committed observer failed")
                        else:
                            _LOGGER.warning("⚠️ Camera images were not persisted")

                except MyVerisureError:
                    raise
                except Exception:
                    _LOGGER.error("❌ Failed to retrieve camera images")
                    
                    refresh_data.append(
                        CameraRefreshData(
                            timestamp=datetime.now().isoformat(),
                            num_images=0,
                            camera_identifier=formatted_code,
                        )
                    )

            _LOGGER.info(
                "🎉 Camera images retrieval completed for %d cameras",
                len(camera_devices_list),
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
                total_cameras=len(camera_devices_list),
                successful_refreshes=successful_refreshes,
                failed_refreshes=len(camera_devices_list) - successful_refreshes,
                timestamp=datetime.now().isoformat(),
            )

        except MyVerisureError:
            raise
        except Exception:
            # Calculate total execution time even in case of error
            total_time = time.time() - start_time
            _LOGGER.error("💥 Failed to refresh camera images")
            _LOGGER.info(
                "⏱️ Total execution time (with error): %.2f seconds",
                total_time
            )
            raise MyVerisureError("Camera image refresh failed") from None

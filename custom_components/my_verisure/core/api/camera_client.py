"""Camera client for My Verisure API."""

import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from .base_client import BaseClient
from .native_profile import ProfileContext
from ..application.photo_notifications import PhotoNotifications
from ..application.models.camera_images import CameraThumbnail
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
)
from ..session_manager import SessionManager
from ..file_manager import FileManager
from .camera_request_policy import CameraRequestPolicy
from .camera_response_interpreter import (
    CameraResponseError,
    interpret_request_response,
    interpret_status_response,
)
from .camera_image_response_interpreter import (
    CameraImageResponseError,
    interpret_photo_response,
    interpret_thumbnail_response,
)
from .camera_request_polling import (
    PollingAction,
    decide_initial_request,
    decide_status,
)
from ..application.camera_image_storage import CameraImageStorage
from ..api.models.dto.camera_request_image_dto import CameraRequestImageResultDTO
from ..log_utils import redact_headers_for_log, should_log_detailed


_LOGGER = logging.getLogger(__name__)

# GraphQL queries and mutations
REQUEST_IMAGES_MUTATION = """
mutation RequestImages($numinst: String!, $panel: String!, $devices: [Int]!, $mediaType: Int, $resolution: Int, $deviceType: Int) {
  xSRequestImages(
    numinst: $numinst
    panel: $panel
    devices: $devices
    mediaType: $mediaType
    resolution: $resolution
    deviceType: $deviceType
  ) {
    res
    msg
    referenceId
  }
}
"""

REQUEST_IMAGES_STATUS_QUERY = """
query RequestImagesStatus($numinst: String!, $panel: String!, $devices: [Int!]!, $referenceId: String!, $counter: Int) {
  xSRequestImagesStatus(
    numinst: $numinst
    panel: $panel
    devices: $devices
    referenceId: $referenceId
    counter: $counter
  ) {
    res
    msg
    numinst
    status
  }
}
"""

# New GraphQL queries for getting images
GET_THUMBNAIL_QUERY = """
query mkGetThumbnail($numinst: String!, $panel: String!, $device: String, $zoneId: String, $idSignal: String) {
  xSGetThumbnail(
    numinst: $numinst
    device: $device
    panel: $panel
    zoneId: $zoneId
    idSignal: $idSignal
  ) {
    idSignal
    deviceId
    deviceCode
    deviceAlias
    timestamp
    signalType
    image
    type
    quality
  }
}
"""

GET_PHOTO_IMAGES_QUERY = """
query mkGetPhotoImages($numinst: String!, $idSignal: String!, $signalType: String!, $panel: String!) {
  xSGetPhotoImages(
    numinst: $numinst
    idsignal: $idSignal
    signaltype: $signalType
    panel: $panel
  ) {
    devices {
      id
      code
      name
      quality
      images {
        id
        image
        type
      }
    }
  }
}
"""


class CameraClient(BaseClient):
    """Client for camera operations."""

    def __init__(
        self,
        session_manager: SessionManager,
        file_manager: FileManager,
        profile_context: ProfileContext | None = None,
        notifications: PhotoNotifications | None = None,
    ) -> None:
        """Initialize the camera client."""
        super().__init__(session_manager=session_manager, profile_context=profile_context)
        self.notifications = notifications
        self._push_thumbnails: dict[tuple[str, str], CameraThumbnail] = {}
        self._capture_started_at = 0.0
        self.last_completion_source = "polling"
        self._file_manager = file_manager
        self._request_policy = CameraRequestPolicy()
        self._image_storage = CameraImageStorage(file_manager)

    def _resolve_file_manager(self) -> FileManager:
        """Return the file manager owned by this composition root."""
        return self._file_manager

    
    async def request_image(
        self, installation_id: str, panel: str, devices: List[int], capabilities: str,
        max_attempts: int = 30, check_interval: int = 20,
    ) -> CameraRequestImageResultDTO:
        """Keep one pending hint scope for the existing bounded request."""
        self._push_thumbnails.clear()
        self._capture_started_at = time.time()
        if self.notifications is not None:
            self.notifications.begin(installation_id, self._capture_started_at)
        try:
            return await self._request_image(
                installation_id, panel, devices, capabilities, max_attempts, check_interval
            )
        finally:
            if self.notifications is not None:
                self.notifications.finish()

    async def _push_thumbnail(
        self, installation_id: str, panel: str, devices: list[int],
        headers: dict[str, str] | None, signal: str,
    ) -> CameraThumbnail | None:
        if len(devices) != 1:
            return None
        result = await self._execute_query_direct(
            GET_THUMBNAIL_QUERY,
            {"numinst": installation_id, "panel": panel, "idSignal": signal}, headers,
        )
        try:
            thumbnail = interpret_thumbnail_response(result)
        except CameraImageResponseError:
            return None
        code = result["data"]["xSGetThumbnail"].get("deviceCode")
        allowed = {f"YP{devices[0]:02d}", f"YR{devices[0]:02d}"}
        if code not in allowed or thumbnail.id_signal != signal or thumbnail.signal_type != "16":
            return None
        try:
            captured = datetime.strptime(thumbnail.timestamp, "%Y-%m-%d %H:%M:%S").replace(
                tzinfo=ZoneInfo("Europe/Madrid")
            ).timestamp()
        except ValueError:
            return None
        if not self._capture_started_at - 5 <= captured <= time.time() + 60:
            return None
        self._push_thumbnails[(installation_id, code)] = thumbnail
        return thumbnail

    async def _request_image(
        self,
        installation_id: str,
        panel: str,
        devices: List[int],
        capabilities: str,
        max_attempts: int = 30,
        check_interval: int = 20,
    ) -> CameraRequestImageResultDTO:
        """Request images from cameras with automatic status checking."""
        try:
            if (
                not isinstance(installation_id, str)
                or not installation_id.strip()
                or not isinstance(panel, str)
                or not panel.strip()
                or not isinstance(capabilities, str)
                or not capabilities.strip()
                or not devices
            ):
                raise MyVerisureError("Camera request context required")
            hash_token, session_data = self._get_current_credentials()
            
            context = self._request_policy.build_context(
                installation_id=installation_id,
                panel=panel,
                devices=devices,
                capabilities=capabilities,
                session_data=session_data,
                hash_token=hash_token,
                header_factory=self._get_session_headers,
            )
            variables = context.variables
            headers = context.headers

            _LOGGER.info("My Verisure API request: RequestImages")
            if should_log_detailed():
                _LOGGER.debug(
                    "RequestImages headers (redacted)=%s",
                    redact_headers_for_log(headers or {}),
                )

            # Step 1: Execute the first mutation with retry logic for "request_already_exists"
            reference_id = None
            for attempt in range(1, max_attempts + 1):
                _LOGGER.info(
                    "📸 Requesting images (attempt %d/%d)",
                    attempt,
                    max_attempts,
                )

                result = await self._execute_query_direct(
                    REQUEST_IMAGES_MUTATION,
                    variables,
                    headers,
                )

                try:
                    accepted = interpret_request_response(result)
                except CameraResponseError as error:
                    decision = decide_initial_request(
                        error.code, attempt, max_attempts
                    )
                    if decision.action is PollingAction.RETRY:
                        if self.notifications is not None:
                            self.notifications.finish()
                        await asyncio.sleep(check_interval)
                        if self.notifications is not None:
                            self._capture_started_at = time.time()
                            self.notifications.begin(installation_id, self._capture_started_at)
                        continue
                    if decision.action is PollingAction.RETURN_FAILURE:
                        return CameraRequestImageResultDTO(
                            success=False,
                            successful_requests=0,
                            reference_id="existing_request",
                        )
                    raise MyVerisureError(error.safe_message) from None

                reference_id = accepted.reference_id
                _LOGGER.info("Camera images request submitted")
                break

            if not reference_id:
                _LOGGER.error("❌ Failed to get reference ID after %d attempts", max_attempts)
                raise MyVerisureError("Failed to get reference ID after maximum attempts")

            # Step 2: Execute the second query (REQUEST_IMAGES_STATUS_QUERY) with polling
            for attempt in range(1, max_attempts + 1):
                _LOGGER.info(
                    "🔍 Checking images status (attempt %d/%d)",
                    attempt,
                    max_attempts,
                )

                # Prepare variables for status check
                status_variables = {
                    "numinst": installation_id,
                    "panel": panel,
                    "devices": devices,
                    "referenceId": reference_id,
                    "counter": attempt,
                }

                # Execute the status query
                status_result = await self._execute_query_direct(
                    REQUEST_IMAGES_STATUS_QUERY,
                    status_variables,
                    headers,
                )
                
                try:
                    status_response = interpret_status_response(status_result)
                except CameraResponseError as error:
                    if error.code == "alarm-manager.error_no_response_to_request":
                        return CameraRequestImageResultDTO(
                            success=False,
                            successful_requests=0,
                            reference_id=reference_id,
                        )
                    raise MyVerisureError(error.safe_message) from None

                status = status_response.result
                message = status_response.message
                decision = decide_status(status, message, attempt, max_attempts)

                if decision.action is PollingAction.COMPLETE:
                    _LOGGER.info(
                        "🎉 Images request completed successfully after %d attempts",
                        attempt,
                    )
                    self.last_completion_source = "polling"
                    return CameraRequestImageResultDTO(
                        success=True,
                        successful_requests=len(devices),
                        reference_id=reference_id,
                    )
                if decision.action is PollingAction.RETURN_FAILURE:
                    _LOGGER.error(
                        "❌ Images request failed after %d attempts",
                        attempt,
                    )
                    return CameraRequestImageResultDTO(
                        success=False,
                        successful_requests=0,
                        reference_id=reference_id,
                    )

                _LOGGER.info(
                    "Images request still in progress; waiting %d seconds",
                    check_interval,
                )
                waited_at = time.monotonic()
                if self.notifications is not None:
                    signal = await self.notifications.wait(check_interval)
                    if signal:
                        thumbnail = await self._push_thumbnail(
                            installation_id, panel, devices, headers, signal
                        )
                        if thumbnail is not None:
                            self.last_completion_source = "push"
                            _LOGGER.info("Photo completion confirmed by push")
                            return CameraRequestImageResultDTO(
                                success=True, successful_requests=len(devices),
                                reference_id=reference_id, signal_id=signal,
                            )
                        remaining = check_interval - (time.monotonic() - waited_at)
                        if remaining > 0:
                            await asyncio.sleep(remaining)
                else:
                    await asyncio.sleep(check_interval)

            # If we get here, we've exceeded max attempts
            _LOGGER.warning(
                "⏰ Images request did not complete within %d attempts (%d seconds)",
                max_attempts,
                max_attempts * check_interval,
            )
            return CameraRequestImageResultDTO(
                success=False,
                successful_requests=0,
                reference_id=reference_id
            )

        except MyVerisureAuthenticationError:
            _LOGGER.error("Authentication failed during camera request")
            raise
        except MyVerisureConnectionError:
            _LOGGER.error("Connection failed during camera request")
            raise
        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Unexpected error during camera request")
            raise MyVerisureError("Camera request failed") from None

    async def get_images(
        self,
        installation_id: str,
        panel: str,
        device: str,
        zone_id: str,
        capabilities: str,
        signal_id: str | None = None,
    ) -> Dict[str, Any]:
        """Get images from a specific camera device."""
        try:
            if (
                not isinstance(installation_id, str)
                or not installation_id.strip()
                or not isinstance(panel, str)
                or not panel.strip()
                or not isinstance(capabilities, str)
                or not capabilities.strip()
                or not isinstance(device, str)
                or not device.strip()
                or not isinstance(zone_id, str)
                or not zone_id.strip()
            ):
                raise MyVerisureError("Camera request context required")
            hash_token, session_data = self._get_current_credentials()
            headers = self._get_session_headers(session_data or {}, hash_token)

            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Step 1: Get thumbnail and idSignal
            thumbnail_variables = {
                "numinst": installation_id,
                "panel": panel,
                "device": device,
                "zoneId": zone_id,
            }

            thumbnail = self._push_thumbnails.pop((installation_id, zone_id), None) if signal_id else None
            if thumbnail is None or thumbnail.id_signal != signal_id:
                if signal_id is not None:
                    if not isinstance(signal_id, str) or not signal_id.isdigit():
                        raise MyVerisureError("Invalid photo signal")
                    thumbnail_variables = {"numinst": installation_id, "panel": panel, "idSignal": signal_id}
                thumbnail_result = await self._execute_query_direct(
                    GET_THUMBNAIL_QUERY, thumbnail_variables, headers,
                )
                try:
                    thumbnail = interpret_thumbnail_response(thumbnail_result)
                except CameraImageResponseError as error:
                    raise MyVerisureError(error.safe_message) from None
                if signal_id and thumbnail_result["data"]["xSGetThumbnail"].get("deviceCode") != zone_id:
                    raise MyVerisureError("Photo does not match the selected camera")
            if signal_id and (thumbnail.id_signal != signal_id or thumbnail.signal_type != "16"):
                raise MyVerisureError("Photo signal could not be confirmed")

            id_signal = thumbnail.id_signal
            signal_type = thumbnail.signal_type
            device_alias = thumbnail.device_alias
            timestamp = thumbnail.timestamp

            timestamp_dir = self._request_policy.image_directory(timestamp)

            # Step 2: Get photo images using idSignal
            photo_variables = {
                "numinst": installation_id,
                "idSignal": id_signal,
                "signalType": signal_type,
                "panel": panel,
            }

            photo_result = await self._execute_query_direct(
                GET_PHOTO_IMAGES_QUERY,
                photo_variables,
                headers,
            )

            try:
                photo_set = interpret_photo_response(photo_result)
            except CameraImageResponseError as error:
                raise MyVerisureError(error.safe_message) from None

            if signal_id:
                raw_devices = photo_result.get("data", {}).get("xSGetPhotoImages", {}).get("devices", [])
                expected = {zone_id, zone_id[2:], str(int(zone_id[2:]))}
                if len(raw_devices) != 1 or str(raw_devices[0].get("code")) not in expected:
                    raise MyVerisureError("Photo does not match the selected camera")

            storage_result = await asyncio.to_thread(
                self._image_storage.save,
                thumbnail,
                photo_set,
                zone_id=zone_id,
                timestamp_directory=timestamp_dir,
            )

            saved_all_images = storage_result.complete
            if not photo_set.images:
                _LOGGER.warning("⚠️ No devices found in photo images response")
                return {
                    "success": saved_all_images,
                    "thumbnail_saved": storage_result.thumbnail_saved,
                    "images_saved": 0,
                    "message": "Thumbnail saved, but no additional images found",
                }

            return {
                "success": saved_all_images,
                "thumbnail_saved": storage_result.thumbnail_saved,
                "images_saved": storage_result.images_saved,
                "total_images": storage_result.total_images,
                "message": "Camera images processed successfully",
            }

        except MyVerisureAuthenticationError:
            _LOGGER.error("Authentication failed during image retrieval")
            raise
        except MyVerisureConnectionError:
            _LOGGER.error("Connection failed during image retrieval")
            raise
        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Unexpected error during image retrieval")
            raise MyVerisureError("Image retrieval failed") from None


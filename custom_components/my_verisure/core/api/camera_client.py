"""Camera client for My Verisure API."""

import asyncio
import logging
from typing import Any, Dict, List

from .base_client import BaseClient
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
)
from ..session_manager import SessionManager
from ..file_manager import FileManager
from ..application.camera_request_policy import CameraRequestPolicy
from ..application.camera_response_interpreter import (
    CameraResponseError,
    interpret_request_response,
    interpret_status_response,
)
from ..application.camera_image_response_interpreter import (
    CameraImageResponseError,
    interpret_photo_response,
    interpret_thumbnail_response,
)
from ..application.camera_request_polling import (
    PollingAction,
    decide_initial_request,
    decide_status,
)
from ..api.models.dto.camera_request_image_dto import CameraRequestImageResultDTO
from ..log_utils import redact_headers_for_log, should_log_detailed, truncate_secret


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
    ) -> None:
        """Initialize the camera client."""
        super().__init__(session_manager=session_manager)
        self._file_manager = file_manager
        self._request_policy = CameraRequestPolicy()

    def _resolve_file_manager(self) -> FileManager:
        """Return the file manager owned by this composition root."""
        return self._file_manager

    
    async def request_image(
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
            hash_token, session_data = self._get_current_credentials()
            
            if not panel:
                _LOGGER.error(
                    "No panel information found for installation %s",
                    installation_id,
                )
                raise MyVerisureError("Panel information required for camera operations")

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
                        str(error), attempt, max_attempts
                    )
                    if decision.action is PollingAction.RETRY:
                        await asyncio.sleep(check_interval)
                        continue
                    if decision.action is PollingAction.RETURN_FAILURE:
                        return CameraRequestImageResultDTO(
                            success=False,
                            successful_requests=0,
                            reference_id="existing_request",
                        )
                    raise MyVerisureError(str(error)) from error

                reference_id = accepted.reference_id
                _LOGGER.info(
                    "Camera images request submitted (reference %s)",
                    truncate_secret(reference_id),
                )
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
                    if "alarm-manager.error_no_response_to_request" in str(error):
                        return CameraRequestImageResultDTO(
                            success=False,
                            successful_requests=0,
                            reference_id=reference_id,
                        )
                    raise MyVerisureError(str(error)) from error

                status = status_response.result
                message = status_response.message
                decision = decide_status(status, message, attempt, max_attempts)

                if decision.action is PollingAction.COMPLETE:
                    _LOGGER.info(
                        "🎉 Images request completed successfully after %d attempts",
                        attempt,
                    )
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
                    "⏳ Images request still in progress. Status: %s, waiting %d seconds...",
                    status,
                    check_interval,
                )
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
        except Exception as e:
            _LOGGER.error("Unexpected error during camera request: %s", e)
            raise MyVerisureError(f"Camera request failed: {str(e)}")

    async def get_images(
        self,
        installation_id: str,
        panel: str,
        device: str,
        zone_id: str,
        capabilities: str,
    ) -> Dict[str, Any]:
        """Get images from a specific camera device."""
        try:
            hash_token, session_data = self._get_current_credentials()
            file_manager = self._resolve_file_manager()

            # Prepare headers
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

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

            thumbnail_result = await self._execute_query_direct(
                GET_THUMBNAIL_QUERY,
                thumbnail_variables,
                headers,
            )

            try:
                thumbnail = interpret_thumbnail_response(
                    thumbnail_result,
                    default_zone=zone_id,
                )
            except CameraImageResponseError as error:
                raise MyVerisureError(str(error)) from error

            id_signal = thumbnail.id_signal
            signal_type = thumbnail.signal_type
            device_alias = thumbnail.device_alias
            timestamp = thumbnail.timestamp
            thumbnail_image = thumbnail.image

            timestamp_dir = self._request_policy.image_directory(timestamp)

            # Save thumbnail image
            device_dir = f"cameras/{zone_id}"
            if thumbnail_image:
                thumbnail_path = f"{device_dir}/{timestamp_dir}/thumbnail.jpg"
                success = file_manager.save_base64_image(thumbnail_path, thumbnail_image)

                if success:
                    _LOGGER.info("💾 Thumbnail saved to: %s", thumbnail_path)
                else:
                    _LOGGER.error("❌ Failed to save thumbnail image")

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
                raise MyVerisureError(str(error)) from error

            images = photo_set.images
            if not images:
                _LOGGER.warning("⚠️ No devices found in photo images response")
                return {
                    "success": True,
                    "device": device,
                    "thumbnail_saved": bool(thumbnail_image),
                    "images_saved": 0,
                    "message": "Thumbnail saved, but no additional images found",
                }

            # Process and save images
            images_saved = 0
            for image in images:
                image_id = image.get("id", "unknown")
                image_data = image.get("image", "")
                
                if image_data:
                    # Save each image with appropriate filename
                    if image_id == "0":
                        image_filename = "1.jpg"
                    elif image_id == "1":
                        image_filename = "2.jpg"
                    elif image_id == "2":
                        image_filename = "3.jpg"
                    else:
                        image_filename = f"imagen_{image_id}.jpg"
                    
                    image_path = f"{device_dir}/{timestamp_dir}/{image_filename}"
                    success = file_manager.save_base64_image(image_path, image_data)
                    
                    if success:
                        _LOGGER.info("💾 Image %s saved to: %s", image_id, image_path)
                        images_saved += 1
                    else:
                        _LOGGER.error("❌ Failed to save image %s", image_id)

            return {
                "success": True,
                "device": device,
                "device_alias": device_alias,
                "timestamp": timestamp,
                "id_signal": id_signal,
                "thumbnail_saved": bool(thumbnail_image),
                "images_saved": images_saved,
                "total_images": len(images),
                "message": f"Successfully processed {images_saved} images for device {device}",
            }

        except MyVerisureAuthenticationError:
            _LOGGER.error("Authentication failed during image retrieval")
            raise
        except MyVerisureConnectionError:
            _LOGGER.error("Connection failed during image retrieval")
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during image retrieval: %s", e)
            raise MyVerisureError(f"Image retrieval failed: {str(e)}")


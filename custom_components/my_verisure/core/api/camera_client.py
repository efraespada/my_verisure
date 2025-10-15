"""Camera client for My Verisure API."""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from .base_client import BaseClient
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
)
from ..session_manager import get_session_manager
from ..file_manager import get_file_manager
from ..api.models.dto.camera_request_image_dto import CameraRequestImageResultDTO


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

    def __init__(self) -> None:
        """Initialize the camera client."""
        super().__init__()
        self._session_manager = get_session_manager()

    async def request_image(
        self,
        installation_id: str,
        panel: str,
        devices: List[int],
        capabilities: str,
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

            _LOGGER.info(
                "Requesting images for installation %s, panel %s, devices %s",
                installation_id,
                panel,
                devices,
            )

            # Step 1: Execute the first query (REQUEST_IMAGES_MUTATION)
            variables = {
                "numinst": installation_id,
                "panel": panel,
                "devices": devices,
            }

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

            # Execute the first mutation
            result = await self._execute_query_direct(
                REQUEST_IMAGES_MUTATION,
                variables,
                headers,
            )

            _LOGGER.info("Request images response: %s", result)

            if not result or "data" not in result or "xSRequestImages" not in result["data"]:
                raise MyVerisureError("Invalid response from camera service")

            response = result["data"]["xSRequestImages"]
            
            # Check for GraphQL errors first
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_message = error.get("message", "Unknown GraphQL error")
                
                if "request_already_exists" in error_message:
                    _LOGGER.info("Camera request already exists, this is normal - continuing with status check")
                    return CameraRequestImageResultDTO(
                        success=True,
                        reference_id="existing_request"
                    )
                else:
                    raise MyVerisureError(f"GraphQL error: {error_message}")

            reference_id = response.get("referenceId")
            if not reference_id:
                return CameraRequestImageResultDTO(
                    success=False,
                    reference_id="none"
                )

            _LOGGER.info(
                "Images request submitted successfully. Reference ID: %s. Starting status checking...",
                reference_id,
            )

            # Prepare variables for status check
            status_variables = {
                "numinst": installation_id,
                "panel": panel,
                "devices": devices,
                "referenceId": reference_id,
                "counter": 1,
            }

            # Execute the status query
            status_result = await self._execute_query_direct(
                REQUEST_IMAGES_STATUS_QUERY,
                status_variables,
                headers,
            )

            _LOGGER.info("Status check response: %s", status_result)
               
            return CameraRequestImageResultDTO(
                success=True,
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
        capabilities: str,
    ) -> Dict[str, Any]:
        """Get images from a specific camera device."""
        try:
            hash_token, session_data = self._get_current_credentials()
            file_manager = get_file_manager()
            
            _LOGGER.info(
                "Getting images for device %s in installation %s",
                device,
                installation_id,
            )

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
                "device": device.split()[0] if " " in device else device,  # Extract device type (YR/YP)
                "zoneId": device,
            }

            thumbnail_result = await self._execute_query_direct(
                GET_THUMBNAIL_QUERY,
                thumbnail_variables,
                headers,
            )

            if not thumbnail_result or "data" not in thumbnail_result or "xSGetThumbnail" not in thumbnail_result["data"]:
                raise MyVerisureError("Invalid response from thumbnail service")

            thumbnail_data = thumbnail_result["data"]["xSGetThumbnail"]
            
            if not thumbnail_data.get("idSignal"):
                error_msg = "No idSignal received from thumbnail query"
                _LOGGER.error(error_msg)
                raise MyVerisureError(error_msg)

            id_signal = thumbnail_data["idSignal"]
            signal_type = thumbnail_data.get("signalType", "16")
            device_alias = thumbnail_data.get("deviceAlias", device)
            timestamp = thumbnail_data.get("timestamp", "")
            thumbnail_image = thumbnail_data.get("image", "")

            # Create timestamp-based directory name (replace spaces and special chars)
            timestamp_dir = timestamp.replace(" ", "_").replace(":", "-").replace("/", "-")
            if not timestamp_dir:
                # Fallback to current timestamp if no timestamp provided
                import datetime
                timestamp_dir = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            _LOGGER.info(
                "Thumbnail received. ID Signal: %s, Signal Type: %s, Device: %s",
                id_signal,
                signal_type,
                device_alias,
            )

            # Save thumbnail image
            if thumbnail_image:
                device_dir = f"cameras/{device}"
                thumbnail_path = f"{device_dir}/{timestamp_dir}/thumbnail.jpg"
                success = file_manager.save_base64_image(thumbnail_path, thumbnail_image)
                
                if success:
                    _LOGGER.info("Thumbnail saved to: %s", thumbnail_path)
                else:
                    _LOGGER.error("Failed to save thumbnail image")

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

            if not photo_result or "data" not in photo_result or "xSGetPhotoImages" not in photo_result["data"]:
                raise MyVerisureError("Invalid response from photo images service")

            photo_data = photo_result["data"]["xSGetPhotoImages"]
            
            if not photo_data.get("devices") or not photo_data["devices"]:
                _LOGGER.warning("No devices found in photo images response")
                return {
                    "success": True,
                    "device": device,
                    "thumbnail_saved": bool(thumbnail_image),
                    "images_saved": 0,
                    "message": "Thumbnail saved, but no additional images found",
                }

            # Process and save images
            images_saved = 0
            device_data = photo_data["devices"][0]  # Get first device
            images = device_data.get("images", [])
            
            _LOGGER.info("Found %d images to save for device %s", len(images), device)

            for image in images:
                image_id = image.get("id", "unknown")
                image_data = image.get("image", "")
                image_type = image.get("type", "BINARY")
                
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
                        _LOGGER.info("Image %s saved to: %s", image_id, image_path)
                        images_saved += 1
                    else:
                        _LOGGER.error("Failed to save image %s", image_id)

            _LOGGER.info(
                "Images processing completed. Device: %s, Images saved: %d",
                device,
                images_saved,
            )

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


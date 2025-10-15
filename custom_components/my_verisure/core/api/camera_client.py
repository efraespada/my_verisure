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
        max_attempts: int = 30,
        check_interval: int = 4,
    ) -> Dict[str, Any]:
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

            # Execute the first mutation
            result = await self._execute_query_direct(
                query=REQUEST_IMAGES_MUTATION,
                variables=variables,
                hash_token=hash_token,
                session_data=session_data,
            )

            if not result or "xSRequestImages" not in result:
                _LOGGER.error("Invalid response from request images mutation")
                raise MyVerisureError("Invalid response from camera service")

            response = result["xSRequestImages"]
            
            if not response.get("res"):
                error_msg = response.get("msg", "Unknown error")
                _LOGGER.error("Failed to request images: %s", error_msg)
                raise MyVerisureError(f"Failed to request images: {error_msg}")

            reference_id = response.get("referenceId")
            if not reference_id:
                _LOGGER.error("No reference ID received from request images")
                raise MyVerisureError("No reference ID received from camera service")

            _LOGGER.info(
                "Images request submitted successfully. Reference ID: %s. Starting status checking...",
                reference_id,
            )

            # Step 2: Execute the second query (REQUEST_IMAGES_STATUS_QUERY) with polling
            for attempt in range(1, max_attempts + 1):
                _LOGGER.debug(
                    "Checking images status (attempt %d/%d)",
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
                    query=REQUEST_IMAGES_STATUS_QUERY,
                    variables=status_variables,
                    hash_token=hash_token,
                    session_data=session_data,
                )

                if not status_result or "xSRequestImagesStatus" not in status_result:
                    _LOGGER.error("Invalid response from images status query")
                    raise MyVerisureError("Invalid response from camera status service")

                status_response = status_result["xSRequestImagesStatus"]
                
                if not status_response.get("res"):
                    error_msg = status_response.get("msg", "Unknown error")
                    _LOGGER.error("Failed to check images status: %s", error_msg)
                    raise MyVerisureError(f"Failed to check images status: {error_msg}")

                status = status_response.get("status", "UNKNOWN")
                _LOGGER.debug(
                    "Images status check completed. Status: %s, Counter: %d",
                    status,
                    attempt,
                )
                
                if status == "OK":
                    _LOGGER.info(
                        "Images request completed successfully after %d attempts",
                        attempt,
                    )
                    return {
                        "success": True,
                        "reference_id": reference_id,
                        "status": status,
                        "attempts": attempt,
                        "message": "Images request completed successfully",
                    }
                elif status == "ERROR":
                    _LOGGER.error(
                        "Images request failed with error status after %d attempts",
                        attempt,
                    )
                    return {
                        "success": False,
                        "reference_id": reference_id,
                        "status": status,
                        "attempts": attempt,
                        "message": "Images request failed with error status",
                    }
                else:
                    _LOGGER.debug(
                        "Images request still in progress. Status: %s, waiting %d seconds...",
                        status,
                        check_interval,
                    )
                    
                    if attempt < max_attempts:
                        await asyncio.sleep(check_interval)

            # If we get here, we've exceeded max attempts
            _LOGGER.warning(
                "Images request did not complete within %d attempts (%d seconds)",
                max_attempts,
                max_attempts * check_interval,
            )
            return {
                "success": False,
                "reference_id": reference_id,
                "status": "TIMEOUT",
                "attempts": max_attempts,
                "message": f"Images request did not complete within {max_attempts} attempts",
            }

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

            # Step 1: Get thumbnail and idSignal
            thumbnail_variables = {
                "numinst": installation_id,
                "panel": panel,
                "device": device.split()[0] if " " in device else device,  # Extract device type (YR/YP)
                "zoneId": device,
            }

            thumbnail_result = await self._execute_query_direct(
                query=GET_THUMBNAIL_QUERY,
                variables=thumbnail_variables,
                hash_token=hash_token,
                session_data=session_data,
            )

            if not thumbnail_result or "xSGetThumbnail" not in thumbnail_result:
                _LOGGER.error("Invalid response from thumbnail query")
                raise MyVerisureError("Invalid response from thumbnail service")

            thumbnail_data = thumbnail_result["xSGetThumbnail"]
            
            if not thumbnail_data.get("idSignal"):
                error_msg = "No idSignal received from thumbnail query"
                _LOGGER.error(error_msg)
                raise MyVerisureError(error_msg)

            id_signal = thumbnail_data["idSignal"]
            signal_type = thumbnail_data.get("signalType", "16")
            device_alias = thumbnail_data.get("deviceAlias", device)
            timestamp = thumbnail_data.get("timestamp", "")
            thumbnail_image = thumbnail_data.get("image", "")

            _LOGGER.info(
                "Thumbnail received. ID Signal: %s, Signal Type: %s, Device: %s",
                id_signal,
                signal_type,
                device_alias,
            )

            # Save thumbnail image
            if thumbnail_image:
                # Create incremental counter for this device
                device_dir = f"cameras/{device}"
                counter = 1
                
                # Find next available counter
                while file_manager.file_exists(f"{device_dir}/{counter}/thumbnail.jpg"):
                    counter += 1
                
                thumbnail_path = f"{device_dir}/{counter}/thumbnail.jpg"
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
                query=GET_PHOTO_IMAGES_QUERY,
                variables=photo_variables,
                hash_token=hash_token,
                session_data=session_data,
            )

            if not photo_result or "xSGetPhotoImages" not in photo_result:
                _LOGGER.error("Invalid response from photo images query")
                raise MyVerisureError("Invalid response from photo images service")

            photo_data = photo_result["xSGetPhotoImages"]
            
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
                        image_filename = "imagen_tiempo_A.jpg"
                    elif image_id == "1":
                        image_filename = "imagen_tiempo_B.jpg"
                    elif image_id == "2":
                        image_filename = "imagen_tiempo_C.jpg"
                    else:
                        image_filename = f"imagen_{image_id}.jpg"
                    
                    image_path = f"{device_dir}/{counter}/{image_filename}"
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


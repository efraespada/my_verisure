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


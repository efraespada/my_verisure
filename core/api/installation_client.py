"""Installation client for My Verisure API."""

import logging
import time
from typing import Any, Dict, List, Optional

from .base_client import BaseClient
from .exceptions import MyVerisureAuthenticationError, MyVerisureError
from .models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
    InstallationsListDTO,
)

_LOGGER = logging.getLogger(__name__)

# GraphQL queries
INSTALLATIONS_QUERY = """
query mkInstallationList {
  xSInstallations {
    installations {
      numinst
      alias
      panel
      type
      name
      surname
      address
      city
      postcode
      province
      email
      phone
      due
      role
    }
  }
}
"""

INSTALLATION_SERVICES_QUERY = """
query Srv($numinst: String!, $uuid: String) {
  xSSrv(numinst: $numinst, uuid: $uuid) {
    res
    msg
    language
    installation {
      numinst
      role
      alias
      status
      panel
      sim
      instIbs
      services {
        idService
        active
        visible
        bde
        isPremium
        codOper
        request
        minWrapperVersion
        unprotectActive
        unprotectDeviceStatus
        instDate
        genericConfig {
          total
          attributes {
            key
            value
          }
        }
        attributes {
          attributes {
            name
            value
            active
          }
        }
      }
      configRepoUser {
        alarmPartitions {
          id
          enterStates
          leaveStates
        }
      }
      capabilities
    }
  }
}
"""


class InstallationClient(BaseClient):
    """Installation client for My Verisure API."""

    def __init__(self) -> None:
        """Initialize the installation client."""
        super().__init__()
        # Cache for installation services
        self._installation_services_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl: int = 540  # 9 minutes default TTL

    def _is_cache_valid(self, installation_id: str) -> bool:
        """Check if cached data for installation is still valid."""
        if installation_id not in self._cache_timestamps:
            return False

        cache_time = self._cache_timestamps[installation_id]
        current_time = time.time()
        age = current_time - cache_time

        return age < self._cache_ttl

    def _get_cached_installation_services(
        self, installation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached installation services data if valid."""
        if self._is_cache_valid(installation_id):
            _LOGGER.debug(
                "Using cached installation services for %s", installation_id
            )
            return self._installation_services_cache.get(installation_id)
        else:
            _LOGGER.debug(
                "Cache expired or not found for installation %s",
                installation_id,
            )
            return None

    def _cache_installation_services(
        self, installation_id: str, data: Dict[str, Any]
    ) -> None:
        """Cache installation services data."""
        self._installation_services_cache[installation_id] = data
        self._cache_timestamps[installation_id] = time.time()
        _LOGGER.debug("Cached installation services for %s", installation_id)

    def clear_installation_services_cache(
        self, installation_id: Optional[str] = None
    ) -> None:
        """Clear installation services cache for specific installation or all."""
        if installation_id:
            if installation_id in self._installation_services_cache:
                del self._installation_services_cache[installation_id]
            if installation_id in self._cache_timestamps:
                del self._cache_timestamps[installation_id]
            _LOGGER.debug("Cleared cache for installation %s", installation_id)
        else:
            self._installation_services_cache.clear()
            self._cache_timestamps.clear()
            _LOGGER.debug("Cleared all installation services cache")

    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set the cache TTL (Time To Live) in seconds."""
        self._cache_ttl = ttl_seconds
        _LOGGER.debug("Cache TTL set to %d seconds", ttl_seconds)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        cache_info = {
            "cache_size": len(self._installation_services_cache),
            "ttl_seconds": self._cache_ttl,
            "cached_installations": list(
                self._installation_services_cache.keys()
            ),
            "cache_timestamps": {},
        }

        for installation_id, timestamp in self._cache_timestamps.items():
            age = time.time() - timestamp
            cache_info["cache_timestamps"][installation_id] = {
                "timestamp": timestamp,
                "age_seconds": age,
                "is_valid": age < self._cache_ttl,
            }

        return cache_info

    async def get_installations(
        self,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> List[InstallationDTO]:
        """Get user installations."""
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        _LOGGER.info("Getting user installations...")

        try:
            # Execute the installations query
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            result = await self._execute_query_direct(
                INSTALLATIONS_QUERY, headers=headers
            )

            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("Failed to get installations: %s", error_msg)
                raise MyVerisureError(
                    f"Failed to get installations: {error_msg}"
                )

            # Check for successful response
            data = result.get("data", {})
            installations_data = data.get("xSInstallations", {})
            installations = installations_data.get("installations", [])

            _LOGGER.info("Found %d installations", len(installations))

            # Log installation details
            for i, installation in enumerate(installations):
                _LOGGER.info(
                    "Installation %d: %s (%s) - %s",
                    i + 1,
                    installation.get("alias", "Unknown"),
                    installation.get("numinst", "Unknown"),
                    installation.get("type", "Unknown"),
                )

            # Convert to DTOs
            installation_dtos = [
                InstallationDTO.from_dict(inst) for inst in installations
            ]
            return installation_dtos

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting installations: %s", e)
            raise MyVerisureError(f"Failed to get installations: {e}") from e

    async def get_installation_services(
        self,
        installation_id: str,
        force_refresh: bool = False,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> InstallationServicesDTO:
        """Get detailed services and configuration for an installation."""
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        if not installation_id:
            raise MyVerisureError("Installation ID is required")

        # Check cache first (unless force refresh is requested)
        if not force_refresh:
            cached_data = self._get_cached_installation_services(
                installation_id
            )
            if cached_data:
                _LOGGER.info(
                    "Returning cached installation services for %s",
                    installation_id,
                )
                return InstallationServicesDTO.from_dict(cached_data)

        # Ensure client is connected
        if not self._client:
            _LOGGER.warning("Client not connected, connecting now...")
            await self.connect()

        _LOGGER.info(
            "Getting services for installation %s (force_refresh=%s)",
            installation_id,
            force_refresh,
        )

        try:
            # Prepare variables
            variables = {"numinst": installation_id}

            # Execute the services query
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            result = await self._execute_query_direct(
                INSTALLATION_SERVICES_QUERY, variables, headers
            )

            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error(
                    "Failed to get installation services: %s", error_msg
                )
                raise MyVerisureError(
                    f"Failed to get installation services: {error_msg}"
                )

            # Check for successful response
            data = result.get("data", {})
            services_data = data.get("xSSrv", {})

            if services_data and services_data.get("res") == "OK":
                installation = services_data.get("installation", {})
                services = installation.get("services", [])

                _LOGGER.info(
                    "Found %d services for installation %s",
                    len(services),
                    installation_id,
                )
                _LOGGER.info(
                    "Installation status: %s",
                    installation.get("status", "Unknown"),
                )
                _LOGGER.info(
                    "Installation panel: %s",
                    installation.get("panel", "Unknown"),
                )

                response_data = {
                    "installation": installation,
                    "services": services,
                    "capabilities": installation.get("capabilities"),
                    "language": services_data.get("language"),
                }

                # Cache the response data
                self._cache_installation_services(
                    installation_id, response_data
                )

                # Convert to DTO
                services_dto = InstallationServicesDTO.from_dict(response_data)
                return services_dto
            else:
                error_msg = (
                    services_data.get("msg", "Unknown error")
                    if services_data
                    else "No response data"
                )
                raise MyVerisureError(
                    f"Failed to get installation services: {error_msg}"
                )

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error(
                "Unexpected error getting installation services: %s", e
            )
            raise MyVerisureError(
                f"Failed to get installation services: {e}"
            ) from e

"""Installation client for My Verisure API."""

import logging
from typing import Any, Dict, List, Optional

from .base_client import BaseClient
from .exceptions import MyVerisureAuthenticationError, MyVerisureError
from .models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
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

    def __init__(self, hash_token: Optional[str] = None, session_data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the installation client."""
        super().__init__()
        self._hash = hash_token
        self._session_data = session_data or {}

    def update_auth_token(self, hash_token: str, session_data: Dict[str, Any]) -> None:
        """Update the authentication token and session data."""
        self._hash = hash_token
        self._session_data = session_data
        _LOGGER.debug("Installation client auth token updated")

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

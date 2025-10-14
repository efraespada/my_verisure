"""Installation client for My Verisure API."""

import logging
from typing import List

from .base_client import BaseClient
from .exceptions import MyVerisureAuthenticationError, MyVerisureError
from .models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
)
from .models.dto.device_dto import DeviceListDTO

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

INSTALLATION_DEVICES_QUERY = """
query xSDeviceList($numinst: String!, $panel: String!) {
  xSDeviceList(numinst: $numinst, panel: $panel) {
    res
    devices {
      id
      code
      name
      type
      subtype
      remoteUse
      idService
      isActive
      serialNumber
      config {
        flags {
          pinCode
          doorbellButton
        }
      }
    }
  }
}
"""


class InstallationClient(BaseClient):
    """Installation client for My Verisure API."""

    def __init__(self) -> None:
        """Initialize the installation client."""
        super().__init__()


    async def get_installations(self) -> List[InstallationDTO]:
        """Get user installations."""
        # Get credentials from SessionManager
        hash_token, session_data = self._get_current_credentials()
        
        _LOGGER.warning("InstallationClient getting credentials from SessionManager:")
        _LOGGER.warning("  - Hash token obtained: %s", hash_token[:50] + "..." if hash_token else "None")
        
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
    ) -> InstallationServicesDTO:
        """Get detailed services and configuration for an installation."""
        # Get credentials from SessionManager
        hash_token, session_data = self._get_current_credentials()
        
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        if not installation_id:
            raise MyVerisureError("Installation ID is required")

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

    async def get_installation_devices(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> DeviceListDTO:
        """Get devices for an installation."""
        # Get credentials from SessionManager
        hash_token, session_data = self._get_current_credentials()
        
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        if not installation_id:
            raise MyVerisureError("Installation ID is required")
        
        if not panel:
            raise MyVerisureError("Panel is required")

        _LOGGER.info(
            "Getting devices for installation %s with panel %s",
            installation_id,
            panel,
        )

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "panel": panel
            }

            # Execute the devices query
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )
            
            # Add capabilities header if provided
            if capabilities and headers:
                headers["x-capabilities"] = capabilities

            result = await self._execute_query_direct(
                INSTALLATION_DEVICES_QUERY, variables, headers
            )

            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error(
                    "Failed to get installation devices: %s", error_msg
                )
                raise MyVerisureError(
                    f"Failed to get installation devices: {error_msg}"
                )

            # Check for successful response
            data = result.get("data", {})
            devices_data = data.get("xSDeviceList", {})

            if devices_data and devices_data.get("res") == "OK":
                devices = devices_data.get("devices", [])

                _LOGGER.info(
                    "Found %d devices for installation %s",
                    len(devices),
                    installation_id,
                )

                # Log device details
                for i, device in enumerate(devices):
                    _LOGGER.info(
                        "Device %d: %s (%s) - %s - Active: %s",
                        i + 1,
                        device.get("name", "Unknown"),
                        device.get("id", "Unknown"),
                        device.get("type", "Unknown"),
                        device.get("isActive", False),
                    )

                response_data = {
                    "res": devices_data.get("res", ""),
                    "devices": devices,
                }

                # Convert to DTO
                devices_dto = DeviceListDTO.from_dict(response_data)
                return devices_dto
            else:
                error_msg = (
                    devices_data.get("msg", "Unknown error")
                    if devices_data
                    else "No response data"
                )
                raise MyVerisureError(
                    f"Failed to get installation devices: {error_msg}"
                )

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error(
                "Unexpected error getting installation devices: %s", e
            )
            raise MyVerisureError(
                f"Failed to get installation devices: {e}"
            ) from e

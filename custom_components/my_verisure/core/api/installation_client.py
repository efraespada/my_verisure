"""Installation client for My Verisure API."""

import logging
from typing import List

from ..session_manager import SessionManager
from .base_client import BaseClient
from .exceptions import MyVerisureAuthenticationError, MyVerisureError
from .models.dto.installation_dto import (
    InstallationDTO,
    DetailedInstallationDTO,
)
from .models.dto.device_dto import DeviceListDTO
from ..application.installation_response_interpreter import (
    InstallationResponseError,
    interpret_devices,
    interpret_installations,
    interpret_services,
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

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialize the installation client."""
        super().__init__(session_manager=session_manager)


    async def get_installations(self) -> List[InstallationDTO]:
        """Get user installations."""
        # Get credentials from SessionManager
        hash_token, session_data = self._get_current_credentials()
        
        # Credentials obtained from SessionManager
        
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        _LOGGER.info("🏠 Getting user installations...")

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

            try:
                installation_records = interpret_installations(result)
            except InstallationResponseError as error:
                raise MyVerisureError(str(error)) from error

            _LOGGER.info("✅ Found %d installations", len(installation_records))
            return [
                InstallationDTO.from_dict(record) for record in installation_records
            ]

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting installations: %s", e)
            raise MyVerisureError(f"Failed to get installations: {e}") from e

    async def get_installation_services(
        self,
        installation_id: str,
        force_refresh: bool = False,
    ) -> DetailedInstallationDTO:
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
            "🔧 Getting services for installation %s (force_refresh=%s)",
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

            try:
                response_data = interpret_services(result)
            except InstallationResponseError as error:
                raise MyVerisureError(str(error)) from error

            installation = response_data["installation"]

            device_list = await self.get_installation_devices(
                installation_id,
                installation.get("panel", "Unknown"),
                installation.get("capabilities", "Unknown"),
            )

            installations_dto = await self.get_installations()
            _LOGGER.info(
                "✅ Found %d devices for installation %s",
                len(device_list.devices),
                installation_id,
            )

            installation_dto = next(
                (item for item in installations_dto if item.numinst == installation_id),
                None,
            )
            if installation_dto is None:
                raise MyVerisureError(f"Installation {installation_id} not found")

            installation["devices"] = [
                device.dict() for device in device_list.devices
            ]
            for field in (
                "type",
                "name",
                "surname",
                "address",
                "city",
                "postcode",
                "province",
                "email",
                "phone",
                "due",
            ):
                installation[field] = getattr(installation_dto, field)

            detailed_response = {
                "installation": installation,
                "language": response_data.get("language"),
            }
            return DetailedInstallationDTO.from_dict(detailed_response)

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

            try:
                device_records = interpret_devices(result)
            except InstallationResponseError as error:
                raise MyVerisureError(str(error)) from error

            return DeviceListDTO.from_dict(
                {"res": "OK", "devices": device_records}
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

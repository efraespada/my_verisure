"""Get installation devices use case implementation."""

import logging
from typing import List
from ...api.models.domain.device import Device
from ...repositories.interfaces.installation_repository import InstallationRepository
from ..interfaces.get_installation_devices_use_case import GetInstallationDevicesUseCase

_LOGGER = logging.getLogger(__name__)


class GetInstallationDevicesUseCaseImpl(GetInstallationDevicesUseCase):
    """Implementation of get installation devices use case."""

    def __init__(self, installation_repository: InstallationRepository):
        """Initialize the use case with required dependencies."""
        self.installation_repository = installation_repository

    async def get_installation_devices(
        self, 
        installation_id: str, 
        force_refresh: bool = False
    ) -> List[Device]:
        """Get devices for an installation."""
        try:
            _LOGGER.info(
                "Getting devices for installation %s (force_refresh=%s)",
                installation_id,
                force_refresh
            )

            # Validate inputs
            if not installation_id:
                raise ValueError("Installation ID is required")

            # Get devices from repository
            detailed_installation = await self.installation_repository.get_installation_services(
                installation_id=installation_id,
                force_refresh=force_refresh
            )

            _LOGGER.info(
                "Successfully retrieved %d devices for installation %s",
                len(detailed_installation.installation.devices),
                installation_id
            )

            # Log device summary
            devices = detailed_installation.installation.devices

            active_devices = [device for device in devices if device.is_active]
            remote_devices = [device for device in devices if device.remote_use]
            
            _LOGGER.info(
                "Device summary: %d total, %d active, %d remote accessible",
                len(devices),
                len(active_devices),
                len(remote_devices)
            )

            # Log device types
            device_types = {}
            for device in devices:
                device_type = device.type
                device_types[device_type] = device_types.get(device_type, 0) + 1
            
            if device_types:
                _LOGGER.info("Device types: %s", device_types)

            return devices

        except ValueError as e:
            _LOGGER.error("Validation error getting installation devices: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting installation devices: %s", e)
            raise

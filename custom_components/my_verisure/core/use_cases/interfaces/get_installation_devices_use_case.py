"""Get installation devices use case interface."""

from abc import ABC, abstractmethod
from typing import Optional

from ...api.models.domain.device import DeviceList


class GetInstallationDevicesUseCase(ABC):
    """Interface for get installation devices use case."""

    @abstractmethod
    async def get_installation_devices(
        self, 
        installation_id: str, 
        force_refresh: bool = False
    ) -> DeviceList:
        """Get devices for an installation."""
        pass

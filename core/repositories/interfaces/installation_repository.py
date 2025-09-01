"""Installation repository interface."""

from abc import ABC, abstractmethod
from typing import List

from api.models.domain.installation import Installation, InstallationServices


class InstallationRepository(ABC):
    """Interface for installation repository."""

    @abstractmethod
    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        pass

    @abstractmethod
    async def get_installation_services(
        self, installation_id: str, force_refresh: bool = False
    ) -> InstallationServices:
        """Get installation services."""
        pass

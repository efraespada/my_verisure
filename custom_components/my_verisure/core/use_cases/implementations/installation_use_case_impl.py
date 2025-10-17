"""Installation use case implementation."""

import logging
from typing import List

from ...api.models.domain.installation import Installation, DetailedInstallation
from ...repositories.interfaces.installation_repository import InstallationRepository
from ..interfaces.installation_use_case import InstallationUseCase

_LOGGER = logging.getLogger(__name__)


class InstallationUseCaseImpl(InstallationUseCase):
    """Implementation of installation use case."""

    def __init__(self, installation_repository: InstallationRepository):
        """Initialize the use case with dependencies."""
        self.installation_repository = installation_repository

    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        try:
            return await self.installation_repository.get_installations()

        except Exception as e:
            _LOGGER.error("Error getting installations: %s", e)
            raise

    async def get_installation_services(
        self, installation_id: str, force_refresh: bool = False
    ) -> DetailedInstallation:
        """Get installation services with caching handled by repository."""
        try:
            return await self.installation_repository.get_installation_services(installation_id, force_refresh)

        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise

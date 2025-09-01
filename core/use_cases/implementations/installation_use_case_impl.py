"""Installation use case implementation."""

import logging
from typing import List

from api.models.domain.installation import Installation, InstallationServices
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from use_cases.interfaces.installation_use_case import InstallationUseCase

_LOGGER = logging.getLogger(__name__)


class InstallationUseCaseImpl(InstallationUseCase):
    """Implementation of installation use case."""

    def __init__(self, installation_repository: InstallationRepository):
        """Initialize the use case with dependencies."""
        self.installation_repository = installation_repository

    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        try:
            _LOGGER.info("Getting user installations")

            installations = (
                await self.installation_repository.get_installations()
            )

            _LOGGER.info("Retrieved %d installations", len(installations))
            return installations

        except Exception as e:
            _LOGGER.error("Error getting installations: %s", e)
            raise

    async def get_installation_services(
        self, installation_id: str, force_refresh: bool = False
    ) -> InstallationServices:
        """Get installation services with caching handled by repository."""
        try:
            _LOGGER.info(
                "Getting services for installation %s (force_refresh=%s)",
                installation_id,
                force_refresh,
            )

            # Get services from repository (cache is handled internally)
            services = (
                await self.installation_repository.get_installation_services(
                    installation_id, force_refresh
                )
            )

            _LOGGER.info(
                "Retrieved services for installation %s",
                installation_id,
            )
            return services

        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise

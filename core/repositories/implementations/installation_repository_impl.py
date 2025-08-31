"""Installation repository implementation."""

import logging
from typing import List, Dict, Any, Optional

from api.models.domain.installation import Installation, InstallationServices
from api.models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
)
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)

_LOGGER = logging.getLogger(__name__)


class InstallationRepositoryImpl(InstallationRepository):
    """Implementation of installation repository."""

    def __init__(self, client):
        """Initialize the repository with a client."""
        self.client = client

    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        try:
            _LOGGER.info("Getting user installations")

            # Debug: Check client state before calling get_installations
            _LOGGER.info(
                "Client hash token present: %s",
                "Yes" if self.client._hash else "No",
            )
            _LOGGER.info("Client session data: %s", self.client._session_data)
            _LOGGER.info(
                "Client connected: %s", "Yes" if self.client._client else "No"
            )

            installations_data = await self.client.get_installations()

            # Convert DTOs to domain models
            installations = []
            for installation_data in installations_data:
                installation_dto = InstallationDTO.from_dict(installation_data)
                installation = Installation.from_dto(installation_dto)
                installations.append(installation)

            _LOGGER.info("Found %d installations", len(installations))
            return installations

        except Exception as e:
            _LOGGER.error("Error getting installations: %s", e)
            raise

    async def get_installation_services(
        self, installation_id: str, force_refresh: bool = False
    ) -> InstallationServices:
        """Get installation services."""
        try:
            _LOGGER.info(
                "Getting services for installation %s (force_refresh=%s)",
                installation_id,
                force_refresh,
            )

            services_data = await self.client.get_installation_services(
                installation_id, force_refresh
            )

            _LOGGER.info("Raw services data received: %s", type(services_data))
            _LOGGER.info(
                "Services data keys: %s",
                (
                    list(services_data.keys())
                    if isinstance(services_data, dict)
                    else "Not a dict"
                ),
            )

            # Convert to domain model
            try:
                services_dto = InstallationServicesDTO.from_dict(services_data)
                _LOGGER.info("DTO conversion successful")
            except Exception as dto_error:
                _LOGGER.error("Error converting to DTO: %s", dto_error)
                raise

            try:
                services = InstallationServices.from_dto(services_dto)
                _LOGGER.info("Domain model conversion successful")
            except Exception as domain_error:
                _LOGGER.error(
                    "Error converting to domain model: %s", domain_error
                )
                raise

            _LOGGER.info(
                "Retrieved services for installation %s", installation_id
            )
            return services

        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        try:
            return self.client.get_cache_info()
        except Exception as e:
            _LOGGER.error("Error getting cache info: %s", e)
            return {}

    def clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear installation services cache."""
        try:
            self.client.clear_installation_services_cache(installation_id)
            _LOGGER.info(
                "Cache cleared for installation: %s", installation_id or "all"
            )
        except Exception as e:
            _LOGGER.error("Error clearing cache: %s", e)

    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL."""
        try:
            self.client.set_cache_ttl(ttl_seconds)
            _LOGGER.info("Cache TTL set to %d seconds", ttl_seconds)
        except Exception as e:
            _LOGGER.error("Error setting cache TTL: %s", e)

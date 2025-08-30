"""Installation use case implementation."""

import logging
from typing import List, Dict, Any, Optional

from api.models.domain.installation import Installation, InstallationServices
from repositories.interfaces.installation_repository import InstallationRepository
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
            
            installations = await self.installation_repository.get_installations()
            
            _LOGGER.info("Retrieved %d installations", len(installations))
            return installations
            
        except Exception as e:
            _LOGGER.error("Error getting installations: %s", e)
            raise
    
    async def get_installation_services(self, installation_id: str, force_refresh: bool = False) -> InstallationServices:
        """Get installation services."""
        try:
            _LOGGER.info("Getting services for installation %s (force_refresh=%s)", installation_id, force_refresh)
            
            services = await self.installation_repository.get_installation_services(installation_id, force_refresh)
            
            _LOGGER.info("Retrieved services for installation %s", installation_id)
            return services
            
        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        try:
            cache_info = self.installation_repository.get_cache_info()
            _LOGGER.debug("Cache info: %s", cache_info)
            return cache_info
            
        except Exception as e:
            _LOGGER.error("Error getting cache info: %s", e)
            return {}
    
    def clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear installation services cache."""
        try:
            self.installation_repository.clear_cache(installation_id)
            _LOGGER.info("Cache cleared for installation: %s", installation_id or "all")
            
        except Exception as e:
            _LOGGER.error("Error clearing cache: %s", e)
    
    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL."""
        try:
            self.installation_repository.set_cache_ttl(ttl_seconds)
            _LOGGER.info("Cache TTL set to %d seconds", ttl_seconds)
            
        except Exception as e:
            _LOGGER.error("Error setting cache TTL: %s", e) 
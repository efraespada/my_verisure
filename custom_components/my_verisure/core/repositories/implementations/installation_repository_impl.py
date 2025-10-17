"""Installation repository implementation."""

import logging
from typing import List, Optional

from ...api.models.domain.installation import Installation, DetailedInstallation
from ...api.models.dto.installation_dto import DetailedInstallationDTO
from ...file_manager import get_file_manager
from ..interfaces.installation_repository import InstallationRepository
from ...utils.jwt_utils import is_jwt_expired

_LOGGER = logging.getLogger(__name__)


class InstallationRepositoryImpl(InstallationRepository):
    """Implementation of installation repository."""

    def __init__(self, client):
        """Initialize the repository with a client."""
        self.client = client
        self._file_manager = get_file_manager()

    def _get_cache_filename(self, installation_id: str) -> str:
        """Get cache filename for a specific installation."""
        return f"detailed_installation_{installation_id}.json"

    def _save_detailed_installation_cache(self, installation_id: str, detailed_installation: DetailedInstallation) -> None:
        """Save detailed installation cache to disk using file_manager."""
        try:
            filename = self._get_cache_filename(installation_id)
            data = detailed_installation.dict()
            
            if self._file_manager.save_json(filename, data):
                _LOGGER.info("💾 Detailed installation cache saved for installation %s", installation_id)
            else:
                _LOGGER.error("💥 Failed to save detailed installation cache for installation %s", installation_id)
        except Exception as e:
            _LOGGER.error("💥 Error saving detailed installation cache: %s", e)

    def _load_detailed_installation_cache(self, installation_id: str) -> Optional[DetailedInstallation]:
        """Load detailed installation cache from disk using file_manager."""
        try:
            filename = self._get_cache_filename(installation_id)
            data = self._file_manager.load_json(filename)

            if data is None:
                _LOGGER.warning("No detailed installation cache found for installation %s", installation_id)
                return None
            
            detailed_installation = DetailedInstallation.from_dto(DetailedInstallationDTO.from_dict(data))
            _LOGGER.info("💾 Loaded detailed installation cache for installation %s", installation_id)
            return detailed_installation
        except Exception as e:
            _LOGGER.error("💥 Error loading detailed installation cache: %s", e)
            return None

    def _clear_detailed_installation_cache(self, installation_id: str) -> None:
        """Clear detailed installation cache from disk."""
        try:
            filename = self._get_cache_filename(installation_id)
            if self._file_manager.delete_file(filename):
                _LOGGER.info("🧹 Cleared detailed installation cache for installation %s", installation_id)
            else:
                _LOGGER.info("No detailed installation cache file to clear for installation %s", installation_id)
        except Exception as e:
            _LOGGER.error("💥 Error clearing detailed installation cache: %s", e)

    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        try:
            installations_data = await self.client.get_installations()

            # Convert DTOs to domain models
            installations = []
            for installation_dto in installations_data:
                installation = Installation.from_dto(installation_dto)
                installations.append(installation)

            _LOGGER.info("✅ Found %d installations", len(installations))
            return installations

        except Exception as e:
            _LOGGER.error("💥 Error getting installations: %s", e)
            raise

    async def get_installation_services(
        self, installation_id: str, force_refresh: bool = False
    ) -> DetailedInstallation:
        """Get detailed installation."""
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_detailed_installation = self._load_detailed_installation_cache(installation_id)
                if cached_detailed_installation:
                    capabilities = cached_detailed_installation.installation.capabilities
                    
                    # Check if capabilities JWT has expired
                    if capabilities and is_jwt_expired(capabilities):
                        _LOGGER.info("🔄 Capabilities JWT expired for installation %s, refreshing data", installation_id)
                        # Clear the cache and continue with fresh data fetch
                        self._clear_detailed_installation_cache(installation_id)
                    else:
                        _LOGGER.info("💾 Using cached detailed installation for installation %s", installation_id)
                        return cached_detailed_installation

            # Fetch fresh data from API
            _LOGGER.info("🔄 Fetching fresh detailed installation data for installation %s", installation_id)
            detailed_installation_dto = await self.client.get_installation_services(
                installation_id, 
                force_refresh
            )
            
            detailed_installation = DetailedInstallation.from_dto(detailed_installation_dto)

            # Cache the fresh data
            self._save_detailed_installation_cache(installation_id, detailed_installation)
            
            return detailed_installation

        except Exception as e:
            _LOGGER.error("💥 Error getting detailed installation: %s", e)
            raise

    def clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear detailed installation cache."""
        try:
            if not installation_id:
                # Clear all detailed installation cache files
                cache_files = self._file_manager.list_files("detailed_installation_*.json")
                for cache_file in cache_files:
                    self._file_manager.delete_file(cache_file)
                _LOGGER.info("🧹 Cleared all detailed installation cache")
            else:
                # Clear specific installation cache
                self._clear_detailed_installation_cache(installation_id)
                
        except Exception as e:
            _LOGGER.error("💥 Error clearing detailed installation cache: %s", e)


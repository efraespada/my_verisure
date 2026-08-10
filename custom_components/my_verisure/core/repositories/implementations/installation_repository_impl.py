"""Installation repository implementation."""

from __future__ import annotations

import logging
from typing import List, Optional

from ...api.mappers.installation_mapper import (
    detailed_installation_from_dto,
    installation_from_dto,
)
from ...api.models.domain.installation import Installation, DetailedInstallation
from ...api.models.dto.installation_dto import DetailedInstallationDTO
from ...file_manager import FileManager
from ..interfaces.installation_repository import InstallationRepository
from ...utils.jwt_utils import is_jwt_expired

_LOGGER = logging.getLogger(__name__)


class InstallationRepositoryImpl(InstallationRepository):
    """Implementation of installation repository."""

    def __init__(
        self, client, file_manager: FileManager
    ):
        """Initialize the repository with a client and file manager."""
        self.client = client
        self._file_manager = file_manager

    def _get_cache_filename(self, installation_id: str) -> str:
        """Get cache filename for a specific installation."""
        return f"detailed_installation_{installation_id}.json"

    async def _async_save_detailed_installation_cache(
        self, installation_id: str, detailed_installation: DetailedInstallation
    ) -> None:
        """Save detailed installation cache to disk using file_manager."""
        try:
            filename = self._get_cache_filename(installation_id)
            data = detailed_installation.dict()

            if await self._file_manager.async_save_json(filename, data):
                _LOGGER.info(
                    "💾 Detailed installation cache saved for installation %s",
                    installation_id,
                )
            else:
                _LOGGER.error(
                    "💥 Failed to save detailed installation cache for installation %s",
                    installation_id,
                )
        except Exception as e:
            _LOGGER.error("💥 Error saving detailed installation cache: %s", e)

    async def _async_load_detailed_installation_cache(
        self, installation_id: str
    ) -> Optional[DetailedInstallation]:
        """Load detailed installation cache from disk using file_manager."""
        try:
            filename = self._get_cache_filename(installation_id)
            data = await self._file_manager.async_load_json(filename)

            if data is None:
                _LOGGER.warning(
                    "No detailed installation cache found for installation %s",
                    installation_id,
                )
                return None

            detailed_installation = detailed_installation_from_dto(
                DetailedInstallationDTO.from_dict(data)
            )
            _LOGGER.info(
                "💾 Loaded detailed installation cache for installation %s",
                installation_id,
            )
            return detailed_installation
        except Exception as e:
            _LOGGER.error("💥 Error loading detailed installation cache: %s", e)
            return None

    async def _async_clear_detailed_installation_cache(
        self, installation_id: str
    ) -> None:
        """Clear detailed installation cache from disk."""
        try:
            filename = self._get_cache_filename(installation_id)
            if await self._file_manager.async_delete_file(filename):
                _LOGGER.info(
                    "🧹 Cleared detailed installation cache for installation %s",
                    installation_id,
                )
            else:
                _LOGGER.info(
                    "No detailed installation cache file to clear for installation %s",
                    installation_id,
                )
        except Exception as e:
            _LOGGER.error("💥 Error clearing detailed installation cache: %s", e)

    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        try:
            installations_data = await self.client.get_installations()

            installations = []
            for installation_dto in installations_data:
                installation = installation_from_dto(installation_dto)
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
            if not force_refresh:
                cached_detailed_installation = (
                    await self._async_load_detailed_installation_cache(installation_id)
                )
                if cached_detailed_installation:
                    capabilities = (
                        cached_detailed_installation.installation.capabilities
                    )

                    if capabilities and is_jwt_expired(capabilities):
                        _LOGGER.info(
                            "🔄 Capabilities JWT expired for installation %s, refreshing data",
                            installation_id,
                        )
                        await self._async_clear_detailed_installation_cache(
                            installation_id
                        )
                    else:
                        _LOGGER.info(
                            "💾 Using cached detailed installation for installation %s",
                            installation_id,
                        )
                        return cached_detailed_installation

            _LOGGER.info(
                "🔄 Fetching fresh detailed installation data for installation %s",
                installation_id,
            )
            detailed_installation_dto = await self.client.get_installation_services(
                installation_id,
                force_refresh,
            )

            detailed_installation = detailed_installation_from_dto(
                detailed_installation_dto
            )

            await self._async_save_detailed_installation_cache(
                installation_id, detailed_installation
            )

            return detailed_installation

        except Exception as e:
            _LOGGER.error("💥 Error getting detailed installation: %s", e)
            raise

    async def clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear detailed installation cache."""
        try:
            if not installation_id:
                cache_files = await self._file_manager.async_list_files(
                    "detailed_installation_*.json"
                )
                for cache_file in cache_files:
                    await self._file_manager.async_delete_file(cache_file)
                _LOGGER.info("🧹 Cleared all detailed installation cache")
            else:
                await self._async_clear_detailed_installation_cache(installation_id)

        except Exception as e:
            _LOGGER.error("💥 Error clearing detailed installation cache: %s", e)

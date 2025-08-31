"""Installation use case implementation."""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple

from api.models.domain.installation import Installation, InstallationServices
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from use_cases.interfaces.installation_use_case import InstallationUseCase

_LOGGER = logging.getLogger(__name__)


class InstallationInfoCache:
    """Cache for installation information to avoid repeated API calls."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default TTL
        """Initialize the cache."""
        self._cache: Dict[str, Tuple[InstallationServices, float]] = (
            {}
        )  # installation_id -> (services, timestamp)
        self._ttl_seconds = ttl_seconds

    def get(self, installation_id: str) -> Optional[InstallationServices]:
        """Get cached installation services if valid."""
        if installation_id not in self._cache:
            return None

        services, timestamp = self._cache[installation_id]
        current_time = time.time()

        if current_time - timestamp > self._ttl_seconds:
            # Cache expired
            del self._cache[installation_id]
            return None

        return services

    def set(
        self, installation_id: str, services: InstallationServices
    ) -> None:
        """Set cached installation services."""
        self._cache[installation_id] = (services, time.time())

    def clear(self, installation_id: Optional[str] = None) -> None:
        """Clear cache for specific installation or all."""
        if installation_id:
            if installation_id in self._cache:
                del self._cache[installation_id]
        else:
            self._cache.clear()

    def set_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL."""
        self._ttl_seconds = ttl_seconds

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        return {
            "cache_size": len(self._cache),
            "ttl_seconds": self._ttl_seconds,
            "cached_installations": list(self._cache.keys()),
        }


class InstallationUseCaseImpl(InstallationUseCase):
    """Implementation of installation use case."""

    def __init__(self, installation_repository: InstallationRepository):
        """Initialize the use case with dependencies."""
        self.installation_repository = installation_repository
        self._installation_cache = InstallationInfoCache()

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
        """Get installation services with caching."""
        try:
            _LOGGER.info(
                "Getting services for installation %s (force_refresh=%s)",
                installation_id,
                force_refresh,
            )

            # Check cache first (unless force_refresh is True)
            if not force_refresh:
                cached_services = self._installation_cache.get(installation_id)
                if cached_services:
                    _LOGGER.debug(
                        "Using cached installation services for %s",
                        installation_id,
                    )
                    return cached_services

            # Get services from repository
            services = (
                await self.installation_repository.get_installation_services(
                    installation_id, force_refresh
                )
            )

            # Cache the result
            self._installation_cache.set(installation_id, services)

            _LOGGER.info(
                "Retrieved and cached services for installation %s",
                installation_id,
            )
            return services

        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        try:
            # Combine repository cache info with our cache info
            repo_cache_info = self.installation_repository.get_cache_info()
            our_cache_info = self._installation_cache.get_cache_info()

            cache_info = {
                "repository_cache": repo_cache_info,
                "use_case_cache": our_cache_info,
            }

            _LOGGER.debug("Cache info: %s", cache_info)
            return cache_info

        except Exception as e:
            _LOGGER.error("Error getting cache info: %s", e)
            return {}

    def clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear installation services cache."""
        try:
            # Clear repository cache
            self.installation_repository.clear_cache(installation_id)

            # Clear our cache
            self._installation_cache.clear(installation_id)

            _LOGGER.info(
                "Cache cleared for installation: %s", installation_id or "all"
            )

        except Exception as e:
            _LOGGER.error("Error clearing cache: %s", e)

    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL."""
        try:
            # Set repository cache TTL
            self.installation_repository.set_cache_ttl(ttl_seconds)

            # Set our cache TTL
            self._installation_cache.set_ttl(ttl_seconds)

            _LOGGER.info("Cache TTL set to %d seconds", ttl_seconds)

        except Exception as e:
            _LOGGER.error("Error setting cache TTL: %s", e)

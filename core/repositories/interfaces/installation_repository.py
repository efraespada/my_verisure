"""Installation repository interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

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

    @abstractmethod
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        pass

    @abstractmethod
    def clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear installation services cache."""
        pass

    @abstractmethod
    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL."""
        pass

"""Installation repository implementation."""

import json
import logging
import os
import time
from typing import List, Dict, Any, Optional

from ...api.models.domain.installation import Installation, InstallationServices
from ...api.models.domain.device import DeviceList

from ..interfaces.installation_repository import InstallationRepository

_LOGGER = logging.getLogger(__name__)


class InstallationRepositoryImpl(InstallationRepository):
    """Implementation of installation repository."""

    def __init__(self, client, cache_dir: str = None):
        """Initialize the repository with a client."""
        self.client = client
        # Simplified cache: only cache InstallationServices objects
        self._services_cache: Dict[str, InstallationServices] = {}
        self._services_timestamp: Optional[float] = None
        self._services_ttl: int = 300  # 5 minutes default TTL
        
        # Setup cache directory
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".my_verisure_cache")
        self._cache_dir = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        
        # Load existing cache from disk
        self._load_cache_from_disk()

    def _get_cache_file_path(self, installation_id: str) -> str:
        """Get cache file path for a specific installation."""
        return os.path.join(self._cache_dir, f"services_{installation_id}.json")

    def _save_cache_to_disk(self, installation_id: str, services: InstallationServices) -> None:
        """Save services cache data to disk."""
        try:
            cache_file = self._get_cache_file_path(installation_id)
            
            serializable_data = {
                "timestamp": time.time(),
                "services": services.dict()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            _LOGGER.info("💾 Services cache saved to disk for installation %s", installation_id)
        except Exception as e:
            _LOGGER.error("💥 Error saving services cache to disk: %s", e)

    def _load_cache_data_from_disk(self, installation_id: str) -> Optional[InstallationServices]:
        """Load services cache data from disk."""
        try:
            cache_file = self._get_cache_file_path(installation_id)
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if cache is still valid
            timestamp = data.get("timestamp", 0)
            if time.time() - timestamp > self._services_ttl:
                _LOGGER.info("Cache expired for installation %s", installation_id)
                return None
            
            # Convert back to InstallationServices object
            if "services" in data:
                services = InstallationServices(**data["services"])
                _LOGGER.info("💾 Loaded services cache from disk for installation %s", installation_id)
                return services
            else:
                _LOGGER.warning("Invalid cache format for installation %s", installation_id)
                return None
                
        except Exception as e:
            _LOGGER.error("💥 Error loading services cache from disk: %s", e)
            return None

    def _is_services_cache_valid(self, installation_id: str) -> bool:
        """Check if services cache is valid for a specific installation."""
        # If no timestamp, cache is invalid
        if not self._services_timestamp:
            return False
            
        # Check TTL
        if time.time() - self._services_timestamp > self._services_ttl:
            return False
            
        # Check if installation is in cache
        if installation_id not in self._services_cache:
            return False
            
        return True

    def _cache_services(self, installation_id: str, services: InstallationServices) -> None:
        """Cache installation services data."""
        self._services_cache[installation_id] = services
        self._services_timestamp = time.time()
        
        # Save to disk
        self._save_cache_to_disk(installation_id, services)
        
        _LOGGER.info("💾 Cached services for installation %s", installation_id)

    def _get_cached_services(self, installation_id: str) -> Optional[InstallationServices]:
        """Get cached services if valid."""
        if not self._is_services_cache_valid(installation_id):
            return None
            
        if installation_id in self._services_cache:
            _LOGGER.info("💾 Using cached services for installation %s", installation_id)
            return self._services_cache[installation_id]
            
        return None

    def _load_cache_from_disk(self) -> None:
        """Load all available services cache from disk."""
        try:
            # Load all services cache files
            cache_files = [f for f in os.listdir(self._cache_dir) if f.startswith("services_") and f.endswith(".json")]
            
            for cache_file in cache_files:
                try:
                    # Extract installation_id from filename
                    installation_id = cache_file.replace("services_", "").replace(".json", "")
                    
                    services = self._load_cache_data_from_disk(installation_id)
                    if services:
                        self._services_cache[installation_id] = services
                        _LOGGER.info("💾 Loaded services cache from disk for installation %s", installation_id)
                except Exception as e:
                    _LOGGER.error("Error loading cache file %s: %s", cache_file, e)
        except Exception as e:
            _LOGGER.error("💥 Error loading cache from disk: %s", e)

    def _clear_cache_file(self, installation_id: str) -> None:
        """Clear cache file from disk."""
        try:
            cache_file = self._get_cache_file_path(installation_id)
            if os.path.exists(cache_file):
                os.remove(cache_file)
                _LOGGER.info("🧹 Removed cache file: %s", cache_file)
        except Exception as e:
            _LOGGER.error("Error removing cache file: %s", e)

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
    ) -> InstallationServices:
        """Get installation services."""
        try:
            if not force_refresh:
                cached_services = self._get_cached_services(installation_id)
                if cached_services:
                    _LOGGER.info("💾 Using cached services for installation %s", installation_id)
                    return cached_services

            services_dto = await self.client.get_installation_services(
                installation_id, 
                force_refresh
            )
            
            services = InstallationServices.from_dto(services_dto)

            self._cache_services(installation_id, services)
            
            return services

        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise

    def _get_cache_info(self) -> Dict[str, Any]:
        """Get cache information (internal method)."""
        try:
            # Add services cache info
            services_cache_info = {
                "services_cache_size": len(self._services_cache),
                "services_ttl_seconds": self._services_ttl,
                "cached_installations": list(self._services_cache.keys()),
                "cache_directory": self._cache_dir,
            }
            
            if self._services_timestamp:
                age = time.time() - self._services_timestamp
                services_cache_info["services_cache_age_seconds"] = age
                services_cache_info["services_cache_expired"] = age > self._services_ttl
            
            cache_info = {
                "services_cache": services_cache_info,
            }
            
            return cache_info
        except Exception as e:
            _LOGGER.error("Error getting cache info: %s", e)
            return {}

    def _clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear installation services cache (internal method)."""
        try:
            if not installation_id:
                # Clear all services cache from memory
                self._services_cache.clear()
                self._services_timestamp = None
                
                # Clear all services cache files from disk
                cache_files = [f for f in os.listdir(self._cache_dir) if f.startswith("services_") and f.endswith(".json")]
                for cache_file in cache_files:
                    try:
                        os.remove(os.path.join(self._cache_dir, cache_file))
                    except Exception as e:
                        _LOGGER.error("Error removing cache file %s: %s", cache_file, e)
                
                _LOGGER.info("🧹 Cleared all services cache")
            else:
                # Clear specific installation services from memory
                if installation_id in self._services_cache:
                    del self._services_cache[installation_id]
                
                # Clear from disk
                self._clear_cache_file(installation_id)
                
                _LOGGER.info("🧹 Cleared services cache for installation: %s", installation_id)
                
        except Exception as e:
            _LOGGER.error("Error clearing cache: %s", e)

    def _set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL (internal method)."""
        try:
            # Set services cache TTL
            self._services_ttl = ttl_seconds
            
            _LOGGER.info("Cache TTL set to %d seconds", ttl_seconds)
        except Exception as e:
            _LOGGER.error("Error setting cache TTL: %s", e)

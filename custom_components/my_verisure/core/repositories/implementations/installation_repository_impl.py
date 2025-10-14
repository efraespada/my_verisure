"""Installation repository implementation."""

import json
import logging
import os
import time
from typing import List, Dict, Any, Optional

from ...api.models.domain.installation import Installation, InstallationServices
from ...api.models.domain.device import DeviceList
from ...api.models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
)
from ...api.models.dto.device_dto import DeviceListDTO
from ...session_manager import get_session_manager
from ..interfaces.installation_repository import InstallationRepository

_LOGGER = logging.getLogger(__name__)


class InstallationRepositoryImpl(InstallationRepository):
    """Implementation of installation repository."""

    def __init__(self, client, cache_dir: str = None):
        """Initialize the repository with a client."""
        self.client = client
        # Cache for installations based on hash
        self._installations_cache: Dict[str, List[Installation]] = {}
        self._installations_hash: Optional[str] = None
        self._installations_timestamp: Optional[float] = None
        self._installations_ttl: int = 3600  # 1 hour default TTL
        
        # Cache for installation services based on hash and installation_id
        self._services_cache: Dict[str, Dict[str, InstallationServices]] = {}
        self._services_timestamps: Dict[str, Dict[str, float]] = {}
        self._services_ttl: int = 300  # 5 minutes default TTL
        
        # Cache for installation devices based on hash, installation_id and panel
        self._devices_cache: Dict[str, Dict[str, DeviceList]] = {}
        self._devices_timestamps: Dict[str, Dict[str, float]] = {}
        self._devices_ttl: int = 300  # 5 minutes default TTL
        
        # Setup cache directory
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".my_verisure_cache")
        self._cache_dir = cache_dir
        os.makedirs(self._cache_dir, exist_ok=True)
        
        # Load existing cache from disk
        self._load_cache_from_disk()

    def _get_cache_file_path(self, hash_token: str, cache_type: str, installation_id: str = None) -> str:
        """Get cache file path for a specific hash and cache type."""
        # Use a shorter hash to avoid filename length issues
        import hashlib
        short_hash = hashlib.md5(hash_token.encode()).hexdigest()[:16]
        
        if installation_id:
            return os.path.join(self._cache_dir, f"{cache_type}_{short_hash}_{installation_id}.json")
        return os.path.join(self._cache_dir, f"{cache_type}_{short_hash}.json")

    def _save_cache_to_disk(self, hash_token: str, cache_type: str, data: Any, installation_id: str = None) -> None:
        """Save cache data to disk."""
        try:
            cache_file = self._get_cache_file_path(hash_token, cache_type, installation_id)
            
            # Convert data to serializable format
            if cache_type == "installations":
                serializable_data = {
                    "timestamp": time.time(),
                    "installations": [installation.dict() for installation in data]
                }
            elif cache_type == "services":
                serializable_data = {
                    "timestamp": time.time(),
                    "services": data.dict()
                }
            else:
                serializable_data = data
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            _LOGGER.debug("Saved %s cache to disk for hash %s", cache_type, hash_token[:20] + "...")
        except Exception as e:
            _LOGGER.error("Error saving cache to disk: %s", e)

    def _load_cache_data_from_disk(self, hash_token: str = None, cache_type: str = "installations", installation_id: str = None) -> Optional[Any]:
        """Load cache data from disk."""
        try:
            if hash_token is None:
                return None
                
            cache_file = self._get_cache_file_path(hash_token, cache_type, installation_id)
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert back to domain objects if needed
            if cache_type == "installations" and "installations" in data:
                installations = []
                for inst_data in data["installations"]:
                    installation = Installation(**inst_data)
                    installations.append(installation)
                return {
                    "timestamp": data.get("timestamp", 0),
                    "data": installations
                }
            elif cache_type == "services" and "services" in data:
                services = InstallationServices(**data["services"])
                return {
                    "timestamp": data.get("timestamp", 0),
                    "data": services
                }
            
            return data
        except Exception as e:
            _LOGGER.error("Error loading cache from disk: %s", e)
            return None

    def _get_current_hash(self) -> Optional[str]:
        """Get current hash from SessionManager."""
        session_manager = get_session_manager()
        return session_manager.hash_token

    def _is_installations_cache_valid(self) -> bool:
        """Check if installations cache is valid."""
        current_hash = self._get_current_hash()
        
        # If no hash, cache is invalid
        if not current_hash:
            return False
            
        # If hash changed, cache is invalid
        if self._installations_hash != current_hash:
            _LOGGER.debug("Installations cache invalid: hash changed from %s to %s", 
                         self._installations_hash, current_hash)
            return False
            
        # If no timestamp, cache is invalid
        if not self._installations_timestamp:
            return False
            
        # Check TTL
        if time.time() - self._installations_timestamp > self._installations_ttl:
            _LOGGER.debug("Installations cache expired: age %d seconds", 
                         time.time() - self._installations_timestamp)
            return False
            
        return True

    def _is_services_cache_valid(self, installation_id: str) -> bool:
        """Check if services cache is valid for a specific installation."""
        current_hash = self._get_current_hash()
        
        # If no hash, cache is invalid
        if not current_hash:
            return False
            
        # If hash not in services cache, cache is invalid
        if current_hash not in self._services_cache:
            return False
            
        # If installation not in hash cache, cache is invalid
        if installation_id not in self._services_cache[current_hash]:
            return False
            
        # If no timestamp, cache is invalid
        if current_hash not in self._services_timestamps or installation_id not in self._services_timestamps[current_hash]:
            return False
            
        # Check TTL
        timestamp = self._services_timestamps[current_hash][installation_id]
        if time.time() - timestamp > self._services_ttl:
            _LOGGER.debug("Services cache expired for installation %s: age %d seconds", 
                         installation_id, time.time() - timestamp)
            return False
            
        return True

    def _cache_installations(self, installations: List[Installation]) -> None:
        """Cache installations data."""
        current_hash = self._get_current_hash()
        if current_hash:
            self._installations_cache[current_hash] = installations
            self._installations_hash = current_hash
            self._installations_timestamp = time.time()
            
            # Save to disk
            self._save_cache_to_disk(current_hash, "installations", installations)
            
            _LOGGER.debug("Cached %d installations for hash %s", 
                         len(installations), current_hash[:20] + "...")

    def _cache_services(self, installation_id: str, services: InstallationServices) -> None:
        """Cache installation services data."""
        current_hash = self._get_current_hash()
        if current_hash:
            # Initialize hash cache if not exists
            if current_hash not in self._services_cache:
                self._services_cache[current_hash] = {}
            if current_hash not in self._services_timestamps:
                self._services_timestamps[current_hash] = {}
            
            self._services_cache[current_hash][installation_id] = services
            self._services_timestamps[current_hash][installation_id] = time.time()
            
            # Save to disk
            self._save_cache_to_disk(current_hash, "services", services, installation_id)
            
            _LOGGER.debug("Cached services for installation %s with hash %s", 
                         installation_id, current_hash[:20] + "...")

    def _get_cached_installations(self) -> Optional[List[Installation]]:
        """Get cached installations if valid."""
        if not self._is_installations_cache_valid():
            return None
            
        current_hash = self._get_current_hash()
        if current_hash and current_hash in self._installations_cache:
            _LOGGER.debug("Using cached installations for hash %s", current_hash[:20] + "...")
            return self._installations_cache[current_hash]
            
        return None

    def _get_cached_services(self, installation_id: str) -> Optional[InstallationServices]:
        """Get cached services if valid."""
        if not self._is_services_cache_valid(installation_id):
            return None
            
        current_hash = self._get_current_hash()
        if current_hash and current_hash in self._services_cache and installation_id in self._services_cache[current_hash]:
            _LOGGER.debug("Using cached services for installation %s with hash %s", 
                         installation_id, current_hash[:20] + "...")
            return self._services_cache[current_hash][installation_id]
            
        return None

    def _load_cache_from_disk(self) -> None:
        """Load all available cache from disk."""
        try:
            current_hash = self._get_current_hash()
            if not current_hash:
                return
            
            # Try to load installations cache
            cache_data = self._load_cache_data_from_disk(current_hash, "installations")
            if cache_data:
                installations = cache_data["data"]
                timestamp = cache_data["timestamp"]
                
                # Check if cache is still valid
                if time.time() - timestamp <= self._installations_ttl:
                    self._installations_cache[current_hash] = installations
                    self._installations_hash = current_hash
                    self._installations_timestamp = timestamp
                    _LOGGER.debug("Loaded %d installations from disk cache", len(installations))
                else:
                    _LOGGER.debug("Disk cache expired, removing cache file")
                    self._clear_cache_file(current_hash, "installations")
            
            # Try to load services cache for all installations
            import hashlib
            short_hash = hashlib.md5(current_hash.encode()).hexdigest()[:16]
            cache_files = [f for f in os.listdir(self._cache_dir) if f.startswith(f"services_{short_hash}")]
            
            for cache_file in cache_files:
                try:
                    # Extract installation_id from filename
                    parts = cache_file.replace(".json", "").split("_")
                    if len(parts) >= 3:
                        installation_id = "_".join(parts[2:])  # Handle installation IDs with underscores
                        
                        cache_data = self._load_cache_data_from_disk(current_hash, "services", installation_id)
                        if cache_data:
                            services = cache_data["data"]
                            timestamp = cache_data["timestamp"]
                            
                            # Check if cache is still valid
                            if time.time() - timestamp <= self._services_ttl:
                                # Initialize hash cache if not exists
                                if current_hash not in self._services_cache:
                                    self._services_cache[current_hash] = {}
                                if current_hash not in self._services_timestamps:
                                    self._services_timestamps[current_hash] = {}
                                
                                self._services_cache[current_hash][installation_id] = services
                                self._services_timestamps[current_hash][installation_id] = timestamp
                                _LOGGER.debug("Loaded services cache from disk for installation %s", installation_id)
                            else:
                                _LOGGER.debug("Disk cache expired for installation %s, removing cache file", installation_id)
                                self._clear_cache_file(current_hash, "services", installation_id)
                except Exception as e:
                    _LOGGER.error("Error loading cache file %s: %s", cache_file, e)
        except Exception as e:
            _LOGGER.error("Error loading cache from disk: %s", e)

    def _clear_cache_file(self, hash_token: str, cache_type: str, installation_id: str = None) -> None:
        """Clear cache file from disk."""
        try:
            cache_file = self._get_cache_file_path(hash_token, cache_type, installation_id)
            if os.path.exists(cache_file):
                os.remove(cache_file)
                _LOGGER.debug("Removed cache file: %s", cache_file)
        except Exception as e:
            _LOGGER.error("Error removing cache file: %s", e)

    async def get_installations(self) -> List[Installation]:
        """Get user installations."""
        try:
            cached_installations = self._get_cached_installations()
            if cached_installations:
                _LOGGER.info("Using cached installations (%d found)", len(cached_installations))
                return cached_installations

            current_hash = self._get_current_hash()
            _LOGGER.info(
                "Hash token present: %s",
                "Yes" if current_hash else "No",
            )

            installations_data = await self.client.get_installations()

            # Convert DTOs to domain models
            installations = []
            for installation_dto in installations_data:
                installation = Installation.from_dto(installation_dto)
                installations.append(installation)

            # Cache the result
            self._cache_installations(installations)

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
            if not force_refresh:
                cached_services = self._get_cached_services(installation_id)
                if cached_services:
                    _LOGGER.info("Using cached services for installation %s", installation_id)
                    return cached_services

            services_data = await self.client.get_installation_services(
                installation_id, 
                force_refresh
            )
            
            services_dto = services_data

            try:
                services = InstallationServices.from_dto(services_dto)
            except Exception as domain_error:
                _LOGGER.error(
                    "Error converting to domain model: %s", domain_error
                )
                raise

            self._cache_services(installation_id, services)
            return services

        except Exception as e:
            _LOGGER.error("Error getting installation services: %s", e)
            raise

    def _get_cache_info(self) -> Dict[str, Any]:
        """Get cache information (internal method)."""
        try:
            # Add installations cache info
            current_hash = self._get_current_hash()
            installations_cache_info = {
                "installations_cache_size": len(self._installations_cache),
                "installations_hash": self._installations_hash[:20] + "..." if self._installations_hash else None,
                "current_hash": current_hash[:20] + "..." if current_hash else None,
                "installations_cache_valid": self._is_installations_cache_valid(),
                "installations_ttl_seconds": self._installations_ttl,
                "cache_directory": self._cache_dir,
            }
            
            if self._installations_timestamp:
                age = time.time() - self._installations_timestamp
                installations_cache_info["installations_cache_age_seconds"] = age
                installations_cache_info["installations_cache_expired"] = age > self._installations_ttl
            
            # Add services cache info
            services_cache_info = {
                "services_cache_size": sum(len(services) for services in self._services_cache.values()),
                "services_ttl_seconds": self._services_ttl,
                "cached_installations": [],
                "cache_timestamps": {},
            }
            
            if current_hash and current_hash in self._services_cache:
                services_cache_info["cached_installations"] = list(self._services_cache[current_hash].keys())
                
                if current_hash in self._services_timestamps:
                    for installation_id, timestamp in self._services_timestamps[current_hash].items():
                        age = time.time() - timestamp
                        services_cache_info["cache_timestamps"][installation_id] = {
                            "timestamp": timestamp,
                            "age_seconds": age,
                            "is_valid": age < self._services_ttl,
                        }
            
            cache_info = {
                "installations_cache": installations_cache_info,
                "services_cache": services_cache_info,
            }
            
            return cache_info
        except Exception as e:
            _LOGGER.error("Error getting cache info: %s", e)
            return {}

    def _clear_cache(self, installation_id: Optional[str] = None) -> None:
        """Clear installation services cache (internal method)."""
        try:
            # Clear installations cache if no specific installation_id or if it's a general clear
            if not installation_id:
                # Clear from memory
                self._installations_cache.clear()
                self._installations_hash = None
                self._installations_timestamp = None
                self._services_cache.clear()
                self._services_timestamps.clear()
                
                # Clear from disk
                current_hash = self._get_current_hash()
                if current_hash:
                    self._clear_cache_file(current_hash, "installations")
                    # Clear all services cache files for this hash
                    import hashlib
                    short_hash = hashlib.md5(current_hash.encode()).hexdigest()[:16]
                    cache_files = [f for f in os.listdir(self._cache_dir) if f.startswith(f"services_{short_hash}")]
                    for cache_file in cache_files:
                        try:
                            os.remove(os.path.join(self._cache_dir, cache_file))
                        except Exception as e:
                            _LOGGER.error("Error removing cache file %s: %s", cache_file, e)
                
                _LOGGER.info("Cleared all installations and services cache")
            else:
                # Clear specific installation services from memory
                current_hash = self._get_current_hash()
                if current_hash and current_hash in self._services_cache:
                    if installation_id in self._services_cache[current_hash]:
                        del self._services_cache[current_hash][installation_id]
                if current_hash and current_hash in self._services_timestamps:
                    if installation_id in self._services_timestamps[current_hash]:
                        del self._services_timestamps[current_hash][installation_id]
                
                # Clear from disk
                if current_hash:
                    self._clear_cache_file(current_hash, "services", installation_id)
                
                _LOGGER.info("Cleared services cache for installation: %s", installation_id)
                
        except Exception as e:
            _LOGGER.error("Error clearing cache: %s", e)

    def _set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set cache TTL (internal method)."""
        try:
            # Set installations cache TTL
            self._installations_ttl = ttl_seconds
            
            # Set services cache TTL
            self._services_ttl = ttl_seconds
            
            # Set devices cache TTL
            self._devices_ttl = ttl_seconds
            
            _LOGGER.info("Cache TTL set to %d seconds", ttl_seconds)
        except Exception as e:
            _LOGGER.error("Error setting cache TTL: %s", e)

    async def get_installation_devices(
        self, installation_id: str, panel: str, force_refresh: bool = False
    ) -> DeviceList:
        """Get installation devices."""
        try:
            # Get current hash for cache key
            current_hash = self._get_current_hash()
            if not current_hash:
                _LOGGER.warning("No session hash available, cannot use cache")
                force_refresh = True

            # Check cache first (unless force refresh)
            if not force_refresh and current_hash:
                cache_key = f"{installation_id}_{panel}"
                
                # Check memory cache
                if (current_hash in self._devices_cache and 
                    cache_key in self._devices_cache[current_hash]):
                    
                    # Check timestamp
                    if (current_hash in self._devices_timestamps and 
                        cache_key in self._devices_timestamps[current_hash]):
                        
                        timestamp = self._devices_timestamps[current_hash][cache_key]
                        if time.time() - timestamp < self._devices_ttl:
                            _LOGGER.info("Returning devices from memory cache")
                            return self._devices_cache[current_hash][cache_key]
                
                # Try to load from disk cache
                try:
                    cache_file = self._get_cache_file_path(current_hash, "devices", cache_key)
                    if os.path.exists(cache_file):
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                        
                        # Check if cache is still valid
                        cache_timestamp = cached_data.get('timestamp', 0)
                        if time.time() - cache_timestamp < self._devices_ttl:
                            _LOGGER.info("Loading devices from disk cache")
                            devices_dto = DeviceListDTO.from_dict(cached_data['data'])
                            devices = DeviceList.from_dto(devices_dto)
                            
                            # Store in memory cache
                            if current_hash not in self._devices_cache:
                                self._devices_cache[current_hash] = {}
                            if current_hash not in self._devices_timestamps:
                                self._devices_timestamps[current_hash] = {}
                            
                            self._devices_cache[current_hash][cache_key] = devices
                            self._devices_timestamps[current_hash][cache_key] = cache_timestamp
                            
                            return devices
                        else:
                            _LOGGER.info("Disk cache expired, will refresh")
                except Exception as e:
                    _LOGGER.warning("Error loading devices from disk cache: %s", e)

            # Fetch from API
            _LOGGER.info("Fetching devices from API for installation %s with panel %s", 
                        installation_id, panel)
            
            services_data = await self.client.get_installation_services(installation_id, force_refresh)
            capabilities = services_data.capabilities
            
            devices_dto = await self.client.get_installation_devices(installation_id, panel, capabilities)
            devices = DeviceList.from_dto(devices_dto)
            
            # Store in cache
            if current_hash:
                cache_key = f"{installation_id}_{panel}"
                
                # Store in memory cache
                if current_hash not in self._devices_cache:
                    self._devices_cache[current_hash] = {}
                if current_hash not in self._devices_timestamps:
                    self._devices_timestamps[current_hash] = {}
                
                self._devices_cache[current_hash][cache_key] = devices
                self._devices_timestamps[current_hash][cache_key] = time.time()
                
                # Store in disk cache
                try:
                    cache_file = self._get_cache_file_path(current_hash, "devices", cache_key)
                    cache_data = {
                        'timestamp': time.time(),
                        'data': devices_dto.to_dict()
                    }
                    
                    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, indent=2, ensure_ascii=False)
                    
                    _LOGGER.info("Devices cached to disk: %s", cache_file)
                except Exception as e:
                    _LOGGER.warning("Error saving devices to disk cache: %s", e)
            
            return devices
            
        except Exception as e:
            _LOGGER.error("Error getting installation devices: %s", e)
            raise

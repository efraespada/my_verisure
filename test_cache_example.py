#!/usr/bin/env python3
"""
Example script demonstrating the caching functionality for installation services.
"""

import asyncio
import logging
from custom_components.my_verisure.api.client import MyVerisureClient

# Configure logging
logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

async def main():
    """Example usage of the caching functionality."""
    
    # Initialize client
    client = MyVerisureClient("your_username", "your_password")
    
    try:
        # Login
        await client.connect()
        login_success = await client.login()
        
        if not login_success:
            _LOGGER.error("Login failed")
            return
        
        # Get installations
        installations = await client.get_installations()
        if not installations:
            _LOGGER.error("No installations found")
            return
        
        installation_id = installations[0]["numinst"]
        _LOGGER.info("Using installation: %s", installation_id)
        
        # First call - will fetch from API and cache
        _LOGGER.info("=== First call to get_installation_services ===")
        services1 = await client.get_installation_services(installation_id)
        _LOGGER.info("Services count: %d", len(services1.get("services", [])))
        
        # Second call - will use cache
        _LOGGER.info("=== Second call to get_installation_services ===")
        services2 = await client.get_installation_services(installation_id)
        _LOGGER.info("Services count: %d", len(services2.get("services", [])))
        
        # Check cache info
        _LOGGER.info("=== Cache Information ===")
        cache_info = client.get_cache_info()
        _LOGGER.info("Cache size: %d", cache_info["cache_size"])
        _LOGGER.info("TTL: %d seconds", cache_info["ttl_seconds"])
        _LOGGER.info("Cached installations: %s", cache_info["cached_installations"])
        
        for inst_id, info in cache_info["cache_timestamps"].items():
            _LOGGER.info("Installation %s: age=%ds, valid=%s", 
                        inst_id, info["age_seconds"], info["is_valid"])
        
        # Force refresh - will bypass cache
        _LOGGER.info("=== Force refresh call ===")
        services3 = await client.get_installation_services(installation_id, force_refresh=True)
        _LOGGER.info("Services count: %d", len(services3.get("services", [])))
        
        # Change cache TTL
        _LOGGER.info("=== Changing cache TTL ===")
        client.set_cache_ttl(60)  # 1 minute
        _LOGGER.info("New TTL: %d seconds", client.get_cache_info()["ttl_seconds"])
        
        # Clear specific installation cache
        _LOGGER.info("=== Clearing specific installation cache ===")
        client.clear_installation_services_cache(installation_id)
        _LOGGER.info("Cache size after clearing: %d", client.get_cache_info()["cache_size"])
        
        # Clear all cache
        _LOGGER.info("=== Clearing all cache ===")
        client.clear_installation_services_cache()
        _LOGGER.info("Cache size after clearing all: %d", client.get_cache_info()["cache_size"])
        
    except Exception as e:
        _LOGGER.error("Error: %s", e)
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 
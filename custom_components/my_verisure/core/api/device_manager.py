"""Device manager for My Verisure API."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import platform
import random
import time
from typing import Any, Dict, Optional

from ..file_manager import FileManager

_LOGGER = logging.getLogger(__name__)

class DeviceManager:
    """Manages device identifiers and device authorization."""

    def __init__(self, file_manager: FileManager) -> None:
        """Initialize the device manager."""
        self._device_identifiers: Optional[Dict[str, Any]] = None
        self._file_manager = file_manager
        # Keep platform discovery scoped to this manager.  A module-level cache
        # would leak host-derived state between ConfigEntry graphs and tests.
        self._platform_string: str | None = None

    def _resolve_file_manager(self) -> FileManager:
        """Return the manager owned by this composition root."""
        if self._file_manager is None:
            raise RuntimeError("DeviceManager requires an entry-scoped FileManager")
        return self._file_manager


    def _platform_string_for_identifiers(self) -> str:
        """Return platform string for seeding (uses cached value when available)."""
        if self._platform_string is None:
            self._platform_string = platform.platform()
        return self._platform_string

    def _generate_device_identifiers(self) -> Dict[str, Any]:
        """Generate device identifiers with improved randomness."""
        # Get system information for seeding
        system_info = {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
            "platform": self._platform_string_for_identifiers(),
            "python_version": platform.python_version(),
        }
        
        # Get additional system-specific information
        try:
            # Get hostname for additional uniqueness
            hostname = os.uname().nodename if hasattr(os, "uname") else platform.node()
        except (AttributeError, OSError):
            hostname = platform.node()
        
        # Create a more complex seed with multiple factors
        seed_components = [
            f"my_verisure_{system_info['system']}",
            f"_{system_info['machine']}",
            f"_{system_info['node']}",
            f"_{hostname}",
            f"_{int(time.time())}",  # Current timestamp
            f"_{random.randint(1000, 9999)}",  # Random component
        ]
        
        # Combine all seed components
        device_seed = "".join(seed_components)
        device_uuid = hashlib.sha256(device_seed.encode()).hexdigest()

        # Generate a more random UUID using system info + randomness
        random_component = random.randint(10000, 99999)
        timestamp_component = int(time.time() * 1000) % 1000000  # Microsecond precision
        
        uuid_seed = f"{device_seed}_{random_component}_{timestamp_component}"
        uuid_hash = hashlib.sha256(uuid_seed.encode()).hexdigest()
        
        # Format as UUID string with better distribution
        formatted_uuid = (
            uuid_hash.upper()[:8]
            + "-"
            + uuid_hash.upper()[8:12]
            + "-"
            + uuid_hash.upper()[12:16]
            + "-"
            + uuid_hash.upper()[16:20]
            + "-"
            + uuid_hash.upper()[20:32]
        )

        # Generate Indigitall UUID with different randomness
        indigitall_components = [
            f"indigitall_{system_info['system']}",
            f"_{system_info['machine']}",
            f"_{random.randint(100000, 999999)}",
            f"_{int(time.time() * 1000000) % 1000000}",
        ]
        
        indigitall_seed = "".join(indigitall_components)
        indigitall_uuid = hashlib.sha256(indigitall_seed.encode()).hexdigest()
        formatted_indigitall = (
            indigitall_uuid[:8]
            + "-"
            + indigitall_uuid[8:12]
            + "-"
            + indigitall_uuid[12:16]
            + "-"
            + indigitall_uuid[16:20]
            + "-"
            + indigitall_uuid[20:32]
        )

        # Generate device name with some randomness
        device_name_suffix = random.randint(100, 999)
        device_name = f"HomeAssistant-{system_info['system']}-{device_name_suffix}"

        return {
            "idDevice": device_uuid,
            "uuid": formatted_uuid,
            "idDeviceIndigitall": formatted_indigitall,
            "deviceName": device_name,
            "deviceBrand": "HomeAssistant",
            "deviceOsVersion": f"{system_info['system']} {platform.release()}",
            "deviceVersion": "10.154.0",
            "deviceType": "",
            "deviceResolution": "",
            "generated_time": int(time.time()),
        }

    def _load_device_identifiers(self) -> bool:
        """Load device identifiers from file (blocking I/O)."""
        try:
            device_data = self._resolve_file_manager().load_device_identifiers()
            if device_data:
                self._device_identifiers = device_data
                _LOGGER.warning("Device identifiers loaded from device_identifiers.json")
                _LOGGER.warning(
                    "Device UUID: %s",
                    self._device_identifiers.get("uuid", "Unknown"),
                )
                return True
            _LOGGER.warning(
                "No device identifiers file found, will generate new ones"
            )
            return False

        except Exception as e:
            _LOGGER.error("Failed to load device identifiers: %s", e)
            return False

    async def _async_load_device_identifiers(self) -> bool:
        """Load device identifiers without blocking the event loop."""
        try:
            device_data = await self._resolve_file_manager().async_load_device_identifiers()
            if device_data:
                self._device_identifiers = device_data
                _LOGGER.warning("Device identifiers loaded from device_identifiers.json")
                _LOGGER.warning(
                    "Device UUID: %s",
                    self._device_identifiers.get("uuid", "Unknown"),
                )
                return True
            _LOGGER.warning(
                "No device identifiers file found, will generate new ones"
            )
            return False
        except Exception as e:
            _LOGGER.error("Failed to load device identifiers: %s", e)
            return False

    def _save_device_identifiers(self) -> None:
        """Save device identifiers to file (blocking I/O)."""
        if not self._device_identifiers:
            _LOGGER.warning("No device identifiers to save")
            return

        try:
            success = self._resolve_file_manager().save_device_identifiers(
                self._device_identifiers
            )
            if success:
                _LOGGER.warning("Device identifiers saved to device_identifiers.json")
            else:
                _LOGGER.error("Failed to save device identifiers to JSON file")

        except Exception as e:
            _LOGGER.error("Failed to save device identifiers: %s", e)

    async def _async_save_device_identifiers(self) -> None:
        """Save device identifiers without blocking the event loop."""
        if not self._device_identifiers:
            _LOGGER.warning("No device identifiers to save")
            return
        try:
            success = await self._resolve_file_manager().async_save_device_identifiers(
                self._device_identifiers
            )
            if success:
                _LOGGER.warning("Device identifiers saved to device_identifiers.json")
            else:
                _LOGGER.error("Failed to save device identifiers to JSON file")
        except Exception as e:
            _LOGGER.error("Failed to save device identifiers: %s", e)

    def ensure_device_identifiers(self) -> None:
        """Ensure device identifiers are loaded or generated (blocking I/O)."""
        if self._device_identifiers is None:
            if not self._load_device_identifiers():
                _LOGGER.warning("Generating new device identifiers")
                self._device_identifiers = self._generate_device_identifiers()
                self._save_device_identifiers()

    async def async_ensure_device_identifiers(self) -> None:
        """Ensure device identifiers are loaded or generated without blocking."""
        if self._platform_string is None:
            self._platform_string = await asyncio.to_thread(platform.platform)

        if self._device_identifiers is None:
            if not await self._async_load_device_identifiers():
                _LOGGER.warning("Generating new device identifiers")
                self._device_identifiers = await asyncio.to_thread(
                    self._generate_device_identifiers
                )
                await self._async_save_device_identifiers()

    def get_device_info(self) -> Dict[str, Any]:
        """Get current device identifiers information."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        identifiers = self._device_identifiers or {}
        return {
            "uuid": identifiers.get("uuid", "Unknown"),
            "device_name": identifiers.get(
                "deviceName", "Unknown"
            ),
            "device_brand": identifiers.get(
                "deviceBrand", "Unknown"
            ),
            "device_os": identifiers.get(
                "deviceOsVersion", "Unknown"
            ),
            "device_version": identifiers.get(
                "deviceVersion", "Unknown"
            ),
            "generated_time": identifiers.get(
                "generated_time", 0
            ),
        }

    def get_device_identifiers(self) -> Dict[str, str]:
        """Get device identifiers for API calls."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        identifiers = self._device_identifiers or {}
        return identifiers.copy()

    def get_login_variables(
        self, session_id: str, lang: str = "es"
    ) -> Dict[str, str]:
        """Get device identifiers for login mutation."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        identifiers = self._device_identifiers or {}
        return {
            "id": session_id,
            "country": "ES",
            "callby": "OWI_10",  # Native app identifier
            "lang": lang,
            "idDevice": identifiers["idDevice"],
            "idDeviceIndigitall": identifiers[
                "idDeviceIndigitall"
            ],
            "deviceType": identifiers["deviceType"],
            "deviceVersion": identifiers["deviceVersion"],
            "deviceResolution": identifiers["deviceResolution"],
            "uuid": identifiers["uuid"],
            "deviceName": identifiers["deviceName"],
            "deviceBrand": identifiers["deviceBrand"],
            "deviceOsVersion": identifiers["deviceOsVersion"],
        }

    def get_validation_variables(self) -> Dict[str, str]:
        """Get device identifiers for device validation."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        identifiers = self._device_identifiers or {}
        return {
            "idDevice": identifiers["idDevice"],
            "idDeviceIndigitall": identifiers[
                "idDeviceIndigitall"
            ],
            "uuid": identifiers["uuid"],
            "deviceName": identifiers["deviceName"],
            "deviceBrand": identifiers["deviceBrand"],
            "deviceOsVersion": identifiers["deviceOsVersion"],
            "deviceVersion": identifiers["deviceVersion"],
        }

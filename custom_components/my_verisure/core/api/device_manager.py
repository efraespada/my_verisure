"""Device manager for My Verisure API."""

import hashlib
import logging
import os
import platform
import random
import time
import uuid
from typing import Dict, Optional

from ..file_manager import get_file_manager

_LOGGER = logging.getLogger(__name__)


class DeviceManager:
    """Manages device identifiers and device authorization."""

    def __init__(self) -> None:
        """Initialize the device manager."""
        self._device_identifiers: Optional[Dict[str, str]] = None
        self._file_manager = get_file_manager()


    def _generate_device_identifiers(self) -> Dict[str, str]:
        """Generate device identifiers with improved randomness."""
        # Get system information for seeding
        system_info = {
            "system": platform.system(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "node": platform.node(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        }
        
        # Get additional system-specific information
        try:
            # Get hostname for additional uniqueness
            hostname = os.uname().nodename if hasattr(os, 'uname') else platform.node()
        except:
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
        """Load device identifiers from file."""
        try:
            device_data = self._file_manager.load_device_identifiers()
            if device_data:
                self._device_identifiers = device_data
                _LOGGER.warning("Device identifiers loaded from device_identifiers.json")
                _LOGGER.warning(
                    "Device UUID: %s",
                    self._device_identifiers.get("uuid", "Unknown"),
                )
                return True
            else:
                _LOGGER.warning(
                    "No device identifiers file found, will generate new ones"
                )
                return False

        except Exception as e:
            _LOGGER.error("Failed to load device identifiers: %s", e)
            return False

    def _save_device_identifiers(self) -> None:
        """Save device identifiers to file."""
        if not self._device_identifiers:
            _LOGGER.warning("No device identifiers to save")
            return

        try:
            success = self._file_manager.save_device_identifiers(self._device_identifiers)
            if success:
                _LOGGER.warning("Device identifiers saved to device_identifiers.json")
            else:
                _LOGGER.error("Failed to save device identifiers to JSON file")

        except Exception as e:
            _LOGGER.error("Failed to save device identifiers: %s", e)


    def ensure_device_identifiers(self) -> None:
        """Ensure device identifiers are loaded or generated."""
        if self._device_identifiers is None:
            # Try to load existing identifiers
            if not self._load_device_identifiers():
                # Generate new identifiers
                _LOGGER.warning("Generating new device identifiers")
                self._device_identifiers = self._generate_device_identifiers()
                self._save_device_identifiers()

    def get_device_info(self) -> Dict[str, str]:
        """Get current device identifiers information."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        return {
            "uuid": self._device_identifiers.get("uuid", "Unknown"),
            "device_name": self._device_identifiers.get(
                "deviceName", "Unknown"
            ),
            "device_brand": self._device_identifiers.get(
                "deviceBrand", "Unknown"
            ),
            "device_os": self._device_identifiers.get(
                "deviceOsVersion", "Unknown"
            ),
            "device_version": self._device_identifiers.get(
                "deviceVersion", "Unknown"
            ),
            "generated_time": self._device_identifiers.get(
                "generated_time", 0
            ),
        }

    def get_device_identifiers(self) -> Dict[str, str]:
        """Get device identifiers for API calls."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        return self._device_identifiers.copy()

    def get_login_variables(
        self, session_id: str, lang: str = "es"
    ) -> Dict[str, str]:
        """Get device identifiers for login mutation."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        return {
            "id": session_id,
            "country": "ES",
            "callby": "OWI_10",  # Native app identifier
            "lang": lang,
            "idDevice": self._device_identifiers["idDevice"],
            "idDeviceIndigitall": self._device_identifiers[
                "idDeviceIndigitall"
            ],
            "deviceType": self._device_identifiers["deviceType"],
            "deviceVersion": self._device_identifiers["deviceVersion"],
            "deviceResolution": self._device_identifiers["deviceResolution"],
            "uuid": self._device_identifiers["uuid"],
            "deviceName": self._device_identifiers["deviceName"],
            "deviceBrand": self._device_identifiers["deviceBrand"],
            "deviceOsVersion": self._device_identifiers["deviceOsVersion"],
        }

    def get_validation_variables(self) -> Dict[str, str]:
        """Get device identifiers for device validation."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        return {
            "idDevice": self._device_identifiers["idDevice"],
            "idDeviceIndigitall": self._device_identifiers[
                "idDeviceIndigitall"
            ],
            "uuid": self._device_identifiers["uuid"],
            "deviceName": self._device_identifiers["deviceName"],
            "deviceBrand": self._device_identifiers["deviceBrand"],
            "deviceOsVersion": self._device_identifiers["deviceOsVersion"],
            "deviceVersion": self._device_identifiers["deviceVersion"],
        }

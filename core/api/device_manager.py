"""Device manager for My Verisure API."""

import hashlib
import json
import logging
import os
import platform
import time
from typing import Dict, Optional

# No imports needed for this module

_LOGGER = logging.getLogger(__name__)


class DeviceManager:
    """Manages device identifiers and device authorization."""

    def __init__(self, user: str) -> None:
        """Initialize the device manager."""
        self.user = user
        self._device_identifiers: Optional[Dict[str, str]] = None

    def _get_device_identifiers_file(self) -> str:
        """Get the path to the device identifiers file."""
        # Use the same directory as session files
        storage_dir = os.path.expanduser("~/.storage")
        if not os.path.exists(storage_dir):
            # Fallback to current directory
            storage_dir = "."

        return os.path.join(
            storage_dir, f"my_verisure_device_{self.user}.json"
        )

    def _generate_device_identifiers(self) -> Dict[str, str]:
        """Generate device identifiers based on user and system info."""
        # Generate consistent device UUID based on user and system info
        device_seed = f"{self.user}_{platform.system()}_{platform.machine()}"
        device_uuid = hashlib.sha256(device_seed.encode()).hexdigest()

        # Format as UUID string
        formatted_uuid = (
            device_uuid.upper()[:8]
            + "-"
            + device_uuid.upper()[8:12]
            + "-"
            + device_uuid.upper()[12:16]
            + "-"
            + device_uuid.upper()[16:20]
            + "-"
            + device_uuid.upper()[20:32]
        )

        # Generate Indigitall UUID (random but consistent for this device)
        indigitall_seed = f"{self.user}_indigitall_{platform.system()}"
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

        return {
            "idDevice": device_uuid,
            "uuid": formatted_uuid,
            "idDeviceIndigitall": formatted_indigitall,
            "deviceName": f"HomeAssistant-{platform.system()}",
            "deviceBrand": "HomeAssistant",
            "deviceOsVersion": f"{platform.system()} {platform.release()}",
            "deviceVersion": "10.154.0",
            "deviceType": "",
            "deviceResolution": "",
            "generated_time": int(time.time()),
        }

    def _load_device_identifiers(self) -> bool:
        """Load device identifiers from file."""
        file_path = self._get_device_identifiers_file()

        if not os.path.exists(file_path):
            _LOGGER.warning(
                "No device identifiers file found, will generate new ones"
            )
            return False

        try:
            with open(file_path, "r") as f:
                self._device_identifiers = json.load(f)

            _LOGGER.warning("Device identifiers loaded from %s", file_path)
            _LOGGER.warning(
                "Device UUID: %s",
                self._device_identifiers.get("uuid", "Unknown"),
            )
            return True

        except Exception as e:
            _LOGGER.error("Failed to load device identifiers: %s", e)
            return False

    def _save_device_identifiers(self) -> None:
        """Save device identifiers to file."""
        if not self._device_identifiers:
            _LOGGER.warning("No device identifiers to save")
            return

        file_path = self._get_device_identifiers_file()

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w") as f:
                json.dump(self._device_identifiers, f, indent=2)

            _LOGGER.warning("Device identifiers saved to %s", file_path)

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

"""Device manager for My Verisure API."""

from __future__ import annotations

import asyncio
import copy
from dataclasses import dataclass
from enum import StrEnum
import hashlib
import logging
import os
import platform
import random
import time
from typing import Any, Dict, Optional, TypeGuard

from .fields import NATIVE_APP_VERSION, NATIVE_OS_VERSION
from .native_profile import NativeProfile, ProfileContext
from .push_storage import PrivatePushStore
from ..file_manager import FileManager
from ..log_utils import redact_sensitive_data

_LOGGER = logging.getLogger(__name__)


class PushBindingState(StrEnum):
    """Safe provider-binding states; transport connectivity is separate."""

    DISABLED = "disabled"
    PENDING = "pending"
    BOUND = "bound"
    REAUTH_REQUIRED = "reauth_required"
    DEGRADED = "degraded"


@dataclass(frozen=True, repr=False)
class PushTokenStage:
    """Private device-address transaction; never project its contents to HA."""

    previous_identifiers: dict[str, Any]
    previous_profile: NativeProfile
    previous_bytes: bytes | None
    candidate_token: str
    generation: int
    changed: bool


class DeviceManager:
    """Manages device identifiers and device authorization."""

    REQUIRED_IDENTIFIER_KEYS = frozenset(
        {
            "idDevice",
            "uuid",
            "idDeviceIndigitall",
            "deviceName",
            "deviceBrand",
            "deviceOsVersion",
            "deviceVersion",
        }
    )

    def __init__(self, file_manager: FileManager, profile_context: ProfileContext | None = None) -> None:
        """Initialize the device manager."""
        self._device_identifiers: Optional[Dict[str, Any]] = None
        self._file_manager = file_manager
        self.profile_context = profile_context or ProfileContext()
        # Keep platform discovery scoped to this manager. A module-level cache
        # would leak host-derived state between ConfigEntry graphs and tests.
        self._platform_string: str | None = None
        self._binding_store = PrivatePushStore(file_manager)
        self._binding_lock = asyncio.Lock()
        self._binding_generation = 0
        self._staged_push_token: PushTokenStage | None = None

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
            "deviceOsVersion": NATIVE_OS_VERSION,
            "deviceVersion": NATIVE_APP_VERSION,
            "generated_time": int(time.time()),
        }

    @classmethod
    def _has_required_identifiers(
        cls, device_data: object
    ) -> TypeGuard[Dict[str, Any]]:
        """Return whether persisted identifiers satisfy API construction needs."""
        return (
            isinstance(device_data, dict)
            and cls.REQUIRED_IDENTIFIER_KEYS <= device_data.keys()
            and all(
                isinstance(device_data[key], str) and device_data[key].strip()
                for key in cls.REQUIRED_IDENTIFIER_KEYS
            )
        )

    def _load_device_identifiers(self) -> bool:
        """Load device identifiers from file (blocking I/O)."""
        try:
            device_data = self._resolve_file_manager().load_device_identifiers()
            if self._has_required_identifiers(device_data):
                self._device_identifiers = device_data
                self.profile_context.select(device_data.get("protocol_profile"))
                _LOGGER.warning("Device identifiers loaded from device_identifiers.json")
                _LOGGER.warning(
                    "Device context loaded (redacted): %s",
                    redact_sensitive_data(
                        {
                            "uuid": self._device_identifiers.get("uuid"),
                            "deviceName": self._device_identifiers.get("deviceName"),
                        }
                    ),
                )
                return True
            _LOGGER.warning(
                "No device identifiers file found, will generate new ones"
            )
            return False

        except Exception:
            _LOGGER.error("Failed to load device identifiers")
            return False

    async def _async_load_device_identifiers(self) -> bool:
        """Load device identifiers without blocking the event loop."""
        try:
            device_data = await self._resolve_file_manager().async_load_device_identifiers()
            if self._has_required_identifiers(device_data):
                self._device_identifiers = device_data
                self.profile_context.select(device_data.get("protocol_profile"))
                _LOGGER.warning("Device identifiers loaded from device_identifiers.json")
                _LOGGER.warning(
                    "Device context loaded (redacted): %s",
                    redact_sensitive_data(
                        {
                            "uuid": self._device_identifiers.get("uuid"),
                            "deviceName": self._device_identifiers.get("deviceName"),
                        }
                    ),
                )
                return True
            _LOGGER.warning(
                "No device identifiers file found, will generate new ones"
            )
            return False
        except Exception:
            _LOGGER.error("Failed to load device identifiers")
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

        except Exception:
            _LOGGER.error("Failed to save device identifiers")

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
        except Exception:
            _LOGGER.error("Failed to save device identifiers")

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
        info: Dict[str, Any] = {}
        fields = {
            "uuid": "uuid",
            "device_name": "deviceName",
            "device_brand": "deviceBrand",
            "device_os": "deviceOsVersion",
            "device_version": "deviceVersion",
        }
        for public_key, provider_key in fields.items():
            value = identifiers.get(provider_key)
            if isinstance(value, str) and value.strip():
                info[public_key] = value
        generated_time = identifiers.get("generated_time")
        if isinstance(generated_time, int) and generated_time > 0:
            info["generated_time"] = generated_time
        return info

    def get_device_identifiers(self) -> Dict[str, str]:
        """Get device identifiers for API calls."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        identifiers = self._device_identifiers or {}
        return identifiers.copy()

    async def async_set_push_token(self, token: str) -> bool:
        """Persist the notification address while retaining the device UUID."""
        stage, changed = await self.async_stage_push_token(token)
        await self.async_commit_staged_push_token(stage)
        return changed

    async def async_stage_push_token(self, token: str) -> tuple[PushTokenStage, bool]:
        """Select a candidate in memory; provider authentication owns acceptance."""
        if not isinstance(token, str) or not 10 <= len(token) <= 4096:
            raise ValueError("Invalid notification token")
        async with self._binding_lock:
            if self._staged_push_token is not None:
                raise RuntimeError("A push address is already staged")
            await self.async_ensure_device_identifiers()
            identifiers = copy.deepcopy(self._device_identifiers or {})
            path = self._resolve_file_manager().get_file_path("device_identifiers.json")

            def read_previous() -> bytes | None:
                try:
                    return path.read_bytes()
                except FileNotFoundError:
                    return None

            previous_bytes = await asyncio.to_thread(read_previous)
            changed = identifiers.get("idDevice") != token or identifiers.get("protocol_profile") != "android"
            self._binding_generation += 1
            stage = PushTokenStage(
                previous_identifiers=identifiers,
                previous_profile=self.profile_context.current,
                previous_bytes=previous_bytes,
                candidate_token=token,
                generation=self._binding_generation,
                changed=changed,
            )
            self._staged_push_token = stage
            self._device_identifiers = {
                **identifiers, "idDevice": token, "protocol_profile": "android",
            }
            self.profile_context.select("android")
            return stage, changed

    def _require_push_stage(self, stage: PushTokenStage) -> None:
        if (
            not isinstance(stage, PushTokenStage)
            or stage.generation != self._binding_generation
            or self._staged_push_token is not stage
        ):
            raise ValueError("Obsolete push binding snapshot")

    async def _restore_push_stage(self, stage: PushTokenStage) -> None:
        self._device_identifiers = copy.deepcopy(stage.previous_identifiers)
        self.profile_context.current = stage.previous_profile
        await self._binding_store.restore_bytes("device_identifiers.json", stage.previous_bytes)
        self._staged_push_token = None

    async def _await_push_restore(self, stage: PushTokenStage) -> bool:
        restoring = asyncio.create_task(self._restore_push_stage(stage))
        cancelled = False
        while True:
            try:
                await asyncio.shield(restoring)
                return cancelled
            except asyncio.CancelledError:
                if restoring.cancelled():
                    raise
                cancelled = True

    async def async_commit_staged_push_token(self, stage: PushTokenStage) -> None:
        """Persist an accepted candidate, restoring prior state on failure/cancel."""
        async with self._binding_lock:
            self._require_push_stage(stage)
            try:
                if stage.changed:
                    await self._binding_store.save(
                        "device_identifiers.json", copy.deepcopy(self._device_identifiers or {}),
                    )
            except BaseException:
                await self._await_push_restore(stage)
                raise
            self._staged_push_token = None

    async def async_rollback_staged_push_token(self, stage: PushTokenStage) -> None:
        """Restore a failed candidate without reverting a newer transaction."""
        async with self._binding_lock:
            if (
                isinstance(stage, PushTokenStage)
                and stage.generation == self._binding_generation
                and self._staged_push_token is None
            ):
                return
            self._require_push_stage(stage)
            if await self._await_push_restore(stage):
                raise asyncio.CancelledError

    def get_login_variables(
        self, session_id: str, lang: str = "es"
    ) -> Dict[str, str]:
        """Get device identifiers for login mutation."""
        if not self._device_identifiers:
            self.ensure_device_identifiers()

        identifiers = self._device_identifiers or {}
        variables: Dict[str, str] = {
            "id": session_id,
            "country": "ES",
            "callby": self.profile_context.current.callby,
            "lang": lang,
            "idDevice": identifiers["idDevice"],
            "idDeviceIndigitall": identifiers["idDeviceIndigitall"],
            "deviceVersion": NATIVE_APP_VERSION,
            "uuid": identifiers["uuid"],
            "deviceName": identifiers["deviceName"],
            "deviceBrand": identifiers["deviceBrand"],
            "deviceOsVersion": self.profile_context.current.os_version,
        }
        for key in ("deviceType", "deviceResolution"):
            value = identifiers.get(key)
            if isinstance(value, str) and value.strip():
                variables[key] = value
        return variables

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
            "deviceOsVersion": self.profile_context.current.os_version,
            "deviceVersion": NATIVE_APP_VERSION,
        }

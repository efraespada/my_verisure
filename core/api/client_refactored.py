"""Refactored client for My Verisure GraphQL API."""

import logging
import time
from typing import Any, Dict, List, Optional

from .auth_client import AuthClient
from .session_client import SessionClient
from .installation_client import InstallationClient
from .alarm_client import AlarmClient
from .device_manager import DeviceManager
from .exceptions import MyVerisureAuthenticationError, MyVerisureError
from .models.dto.auth_dto import AuthDTO, PhoneDTO
from .models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
)
from .models.dto.session_dto import SessionDTO

_LOGGER = logging.getLogger(__name__)


class MyVerisureClientRefactored:
    """Refactored client for My Verisure GraphQL API."""

    def __init__(self, user: str, password: str) -> None:
        """Initialize the My Verisure client."""
        self.user = user
        self.password = password

        # Initialize specialized clients
        self._auth_client = AuthClient(user, password)
        self._session_client = SessionClient(user)
        self._installation_client = InstallationClient()
        self._alarm_client = AlarmClient()
        self._device_manager = DeviceManager(user)

        # Session state
        self._hash: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._session_data: Dict[str, Any] = {}
        self._otp_data: Optional[Dict[str, Any]] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to My Verisure API."""
        await self._auth_client.connect()
        await self._session_client.connect()
        await self._installation_client.connect()
        await self._alarm_client.connect()

    async def disconnect(self) -> None:
        """Disconnect from My Verisure API."""
        await self._auth_client.disconnect()
        await self._session_client.disconnect()
        await self._installation_client.disconnect()
        await self._alarm_client.disconnect()

    # Authentication methods
    async def login(self) -> AuthDTO:
        """Login to My Verisure API."""
        try:
            auth_result = await self._auth_client.login()

            # Update internal state
            self._hash = auth_result.hash
            self._refresh_token = auth_result.refresh_token
            self._session_data = {
                "user": self.user,
                "lang": auth_result.lang or "ES",
                "legals": auth_result.legals or False,
                "changePassword": auth_result.change_password or False,
                "needDeviceAuthorization": auth_result.need_device_authorization
                or False,
                "login_time": int(time.time()),
            }

            return auth_result

        except Exception as e:
            _LOGGER.error("Login failed: %s", e)
            raise

    def get_available_phones(self) -> List[PhoneDTO]:
        """Get available phone numbers for OTP."""
        return self._auth_client.get_available_phones()

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        return self._auth_client.select_phone(phone_id)

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        return await self._auth_client.send_otp(record_id, otp_hash)

    async def verify_otp(self, otp_code: str) -> AuthDTO:
        """Verify the OTP code received via SMS."""
        try:
            auth_result = await self._auth_client.verify_otp(otp_code)

            # Update internal state
            self._hash = auth_result.hash
            self._refresh_token = auth_result.refresh_token
            self._session_data = {
                "user": self.user,
                "lang": auth_result.lang or "ES",
                "legals": auth_result.legals or False,
                "changePassword": auth_result.change_password or False,
                "needDeviceAuthorization": auth_result.need_device_authorization
                or False,
                "login_time": int(time.time()),
            }

            return auth_result

        except Exception as e:
            _LOGGER.error("OTP verification failed: %s", e)
            raise

    # Session management methods
    async def save_session(self) -> None:
        """Save session data to file."""
        await self._session_client.save_session(
            session_data=self._session_data,
            hash_token=self._hash,
            refresh_token=self._refresh_token,
            device_identifiers=self._device_manager.get_device_identifiers(),
        )

    async def load_session(self) -> bool:
        """Load session data from file."""
        session_data = await self._session_client.load_session()
        if session_data:
            self._session_data = session_data.get("session_data", {})
            self._hash = session_data.get("hash")
            self._refresh_token = self._session_data.get("refreshToken")

            # Load device identifiers if available
            device_identifiers = session_data.get("device_identifiers")
            if device_identifiers:
                self._device_manager._device_identifiers = device_identifiers

            return True
        return False

    def is_session_valid(self) -> bool:
        """Check if current session is still valid."""
        return self._session_client.is_session_valid(
            self._session_data, self._hash
        )

    # Installation methods
    async def get_installations(self) -> List[InstallationDTO]:
        """Get user installations."""
        return await self._installation_client.get_installations(
            hash_token=self._hash, session_data=self._session_data
        )

    async def get_installation_services(
        self, installation_id: str, force_refresh: bool = False
    ) -> InstallationServicesDTO:
        """Get detailed services and configuration for an installation."""
        return await self._installation_client.get_installation_services(
            installation_id=installation_id,
            force_refresh=force_refresh,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    # Cache management methods
    def clear_installation_services_cache(
        self, installation_id: Optional[str] = None
    ) -> None:
        """Clear installation services cache for specific installation or all."""
        self._installation_client.clear_installation_services_cache(
            installation_id
        )

    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """Set the cache TTL (Time To Live) in seconds."""
        self._installation_client.set_cache_ttl(ttl_seconds)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return self._installation_client.get_cache_info()

    # Alarm methods
    async def get_alarm_status(
        self, installation_id: str, capabilities: str
    ) -> Dict[str, Any]:
        """Get alarm status from installation services and real-time check."""
        return await self._alarm_client.get_alarm_status(
            installation_id=installation_id,
            capabilities=capabilities,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    async def send_alarm_command(
        self, installation_id: str, request: str, current_status: str = "E"
    ) -> bool:
        """Send an alarm command to the specified installation."""
        return await self._alarm_client.send_alarm_command(
            installation_id=installation_id,
            request=request,
            current_status=current_status,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    async def disarm_alarm(self, installation_id: str) -> bool:
        """Disarm the alarm for the specified installation."""
        return await self._alarm_client.disarm_alarm(
            installation_id=installation_id,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    async def arm_alarm_away(self, installation_id: str) -> bool:
        """Arm the alarm in away mode for the specified installation."""
        return await self._alarm_client.arm_alarm_away(
            installation_id=installation_id,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    async def arm_alarm_home(self, installation_id: str) -> bool:
        """Arm the alarm in home mode for the specified installation."""
        return await self._alarm_client.arm_alarm_home(
            installation_id=installation_id,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    async def arm_alarm_night(self, installation_id: str) -> bool:
        """Arm the alarm in night mode for the specified installation."""
        return await self._alarm_client.arm_alarm_night(
            installation_id=installation_id,
            hash_token=self._hash,
            session_data=self._session_data,
        )

    # Device management methods
    def get_device_info(self) -> Dict[str, str]:
        """Get current device identifiers information."""
        return self._device_manager.get_device_info()

    # Getters for internal state (for backward compatibility)
    @property
    def hash(self) -> Optional[str]:
        """Get the current hash token."""
        return self._hash

    @property
    def refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        return self._refresh_token

    @property
    def session_data(self) -> Dict[str, Any]:
        """Get the current session data."""
        return self._session_data.copy()

    @property
    def otp_data(self) -> Optional[Dict[str, Any]]:
        """Get the current OTP data."""
        return self._otp_data.copy() if self._otp_data else None

    @property
    def device_identifiers(self) -> Optional[Dict[str, str]]:
        """Get the current device identifiers."""
        return self._device_manager.get_device_identifiers()

    @property
    def installation_services_cache(self) -> Dict[str, Dict[str, Any]]:
        """Get the installation services cache."""
        return self._installation_client._installation_services_cache.copy()

    @property
    def cache_timestamps(self) -> Dict[str, float]:
        """Get the cache timestamps."""
        return self._installation_client._cache_timestamps.copy()

    @property
    def cache_ttl(self) -> int:
        """Get the cache TTL."""
        return self._installation_client._cache_ttl

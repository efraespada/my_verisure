"""Authentication repository interface."""

from abc import ABC, abstractmethod

from api.models.domain.auth import Auth, AuthResult
from api.models.domain.session import DeviceIdentifiers


class AuthRepository(ABC):
    """Interface for authentication repository."""

    @abstractmethod
    async def login(
        self, auth: Auth, device_identifiers: DeviceIdentifiers
    ) -> AuthResult:
        """Login with username and password."""
        pass

    @abstractmethod
    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        pass

    @abstractmethod
    async def verify_otp(
        self,
        otp_code: str,
        otp_hash: str,
        device_identifiers: DeviceIdentifiers,
    ) -> AuthResult:
        """Verify OTP code."""
        pass

    @abstractmethod
    async def validate_device(
        self, device_identifiers: DeviceIdentifiers
    ) -> AuthResult:
        """Validate device with the API."""
        pass

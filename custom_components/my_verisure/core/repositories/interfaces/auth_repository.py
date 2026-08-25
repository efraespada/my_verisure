"""Authentication repository interface."""

from abc import ABC, abstractmethod

from ...application.models.auth import Auth, AuthResult

class AuthRepository(ABC):
    """Interface for authentication repository."""

    @abstractmethod
    async def login(
        self, auth: Auth
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
        otp_code: str
    ) -> AuthResult:
        """Verify OTP code."""
        pass

    @abstractmethod
    def invalidate_otp_challenge(self) -> None:
        """Invalidate all provider-client OTP state for this flow."""
        pass

    @abstractmethod
    def get_available_phones(self) -> list[dict[str, object]]:
        """Return phone numbers available for OTP verification."""
        pass

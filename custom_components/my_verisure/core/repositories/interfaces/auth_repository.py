"""Authentication repository interface."""

from abc import ABC, abstractmethod

from ...api.models.domain.auth import Auth, AuthResult

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

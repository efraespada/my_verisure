"""Authentication use case interface."""

from abc import ABC, abstractmethod
from typing import List

from api.models.domain.auth import AuthResult


class AuthUseCase(ABC):
    """Interface for authentication use case."""

    @abstractmethod
    async def login(self, username: str, password: str) -> AuthResult:
        """Login with username and password."""
        pass

    @abstractmethod
    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        pass

    @abstractmethod
    async def verify_otp(self, otp_code: str) -> bool:
        """Verify OTP code."""
        pass

    @abstractmethod
    def get_available_phones(self) -> List[dict]:
        """Get available phone numbers for OTP."""
        pass

    @abstractmethod
    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        pass

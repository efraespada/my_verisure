"""Session repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from api.models.domain.session import SessionData


class SessionRepository(ABC):
    """Interface for session repository."""

    @abstractmethod
    async def load_session(self, file_path: str) -> Optional[SessionData]:
        """Load session data from file."""
        pass

    @abstractmethod
    async def save_session(
        self, file_path: str, session_data: SessionData
    ) -> bool:
        """Save session data to file."""
        pass

    @abstractmethod
    def is_session_valid(self, session_data: SessionData) -> bool:
        """Check if session data is valid."""
        pass

"""Session use case interface."""

from abc import ABC, abstractmethod

# No imports needed for this interface


class SessionUseCase(ABC):
    """Interface for session use case."""

    @abstractmethod
    async def load_session(self, file_path: str) -> bool:
        """Load session data from file."""
        pass

    @abstractmethod
    async def save_session(self, file_path: str) -> bool:
        """Save session data to file."""
        pass

    @abstractmethod
    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        pass

    @abstractmethod
    async def refresh_session(self) -> bool:
        """Refresh the current session."""
        pass

"""Session use case implementation."""

import logging
from typing import Optional

from api.models.domain.session import SessionData
from repositories.interfaces.session_repository import SessionRepository
from use_cases.interfaces.session_use_case import SessionUseCase

_LOGGER = logging.getLogger(__name__)


class SessionUseCaseImpl(SessionUseCase):
    """Implementation of session use case."""

    def __init__(self, session_repository: SessionRepository):
        """Initialize the use case with dependencies."""
        self.session_repository = session_repository
        self._current_session_data: Optional[SessionData] = None

    async def load_session(self, file_path: str) -> bool:
        """Load session data from file."""
        try:
            _LOGGER.info("Loading session from: %s", file_path)

            session_data = await self.session_repository.load_session(
                file_path
            )

            if session_data:
                self._current_session_data = session_data
                _LOGGER.info("Session loaded successfully")
                return True
            else:
                _LOGGER.info("No session found at: %s", file_path)
                return False

        except Exception as e:
            _LOGGER.error("Error loading session: %s", e)
            return False

    async def save_session(self, file_path: str) -> bool:
        """Save session data to file."""
        try:
            _LOGGER.info("Saving session to: %s", file_path)

            if not self._current_session_data:
                _LOGGER.warning("No session data to save")
                return False

            result = await self.session_repository.save_session(
                file_path, self._current_session_data
            )

            if result:
                _LOGGER.info("Session saved successfully")
            else:
                _LOGGER.error("Failed to save session")

            return result

        except Exception as e:
            _LOGGER.error("Error saving session: %s", e)
            return False

    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        try:
            if not self._current_session_data:
                _LOGGER.debug("No session data available")
                return False

            result = self.session_repository.is_session_valid(
                self._current_session_data
            )

            if result:
                _LOGGER.debug("Session is valid")
            else:
                _LOGGER.debug("Session is invalid")

            return result

        except Exception as e:
            _LOGGER.error("Error checking session validity: %s", e)
            return False

    async def refresh_session(self) -> bool:
        """Refresh the current session."""
        try:
            _LOGGER.info("Refreshing session")

            # This would typically involve re-authenticating with
            # stored credentials.
            # For now, we'll just return True if we have session data
            if self._current_session_data:
                _LOGGER.info("Session refresh completed")
                return True
            else:
                _LOGGER.warning("No session data to refresh")
                return False

        except Exception as e:
            _LOGGER.error("Error refreshing session: %s", e)
            return False

    def get_current_session_data(self) -> Optional[SessionData]:
        """Get current session data."""
        return self._current_session_data

    def set_current_session_data(self, session_data: SessionData) -> None:
        """Set current session data."""
        self._current_session_data = session_data

"""Session repository implementation."""

import logging
import time
from typing import Optional

from api.models.domain.session import SessionData
from repositories.interfaces.session_repository import SessionRepository

_LOGGER = logging.getLogger(__name__)


class SessionRepositoryImpl(SessionRepository):
    """Implementation of session repository."""

    def __init__(self, client):
        """Initialize the repository with a client."""
        self.client = client

    async def load_session(self, file_path: str) -> Optional[SessionData]:
        """Load session data from file."""
        try:
            _LOGGER.info("Loading session from: %s", file_path)

            result = await self.client.load_session(file_path)

            if result:
                # Convert client session data to domain model
                session_data = SessionData(
                    cookies=self.client._cookies,
                    session_data=self.client._session_data,
                    hash=self.client._hash,
                    user=self.client.user,
                    device_identifiers=None,  # Will be loaded from session data
                    saved_time=int(time.time()),
                )

                # Load device identifiers if available
                if self.client._device_identifiers:
                    from api.models.domain.session import DeviceIdentifiers
                    from api.models.dto.session_dto import DeviceIdentifiersDTO

                    device_dto = DeviceIdentifiersDTO.from_dict(
                        self.client._device_identifiers
                    )
                    session_data.device_identifiers = (
                        DeviceIdentifiers.from_dto(device_dto)
                    )

                _LOGGER.info("Session loaded successfully")
                return session_data
            else:
                _LOGGER.info("No session found at: %s", file_path)
                return None

        except Exception as e:
            _LOGGER.error("Error loading session: %s", e)
            return None

    async def save_session(
        self, file_path: str, session_data: SessionData
    ) -> bool:
        """Save session data to file."""
        try:
            _LOGGER.info("Saving session to: %s", file_path)

            # Update client with session data
            self.client._cookies = session_data.cookies
            self.client._session_data = session_data.session_data
            self.client._hash = session_data.hash
            self.client.user = session_data.user

            # Save device identifiers if available
            if session_data.device_identifiers:
                self.client._device_identifiers = (
                    session_data.device_identifiers.to_dto().to_dict()
                )

            # Call client's save method
            await self.client.save_session(file_path)

            _LOGGER.info("Session saved successfully")
            return True

        except Exception as e:
            _LOGGER.error("Error saving session: %s", e)
            return False

    def is_session_valid(self, session_data: SessionData) -> bool:
        """Check if session data is valid."""
        try:
            # Check if we have a hash
            if not session_data.hash:
                _LOGGER.debug("No hash in session data")
                return False

            # Check if session is not too old (6 minutes)
            current_time = int(time.time())
            session_age = current_time - session_data.saved_time

            if session_age > 360:  # 6 minutes
                _LOGGER.debug("Session expired (age: %d seconds)", session_age)
                return False

            _LOGGER.debug(
                "Session appears valid (age: %d seconds)", session_age
            )
            return True

        except Exception as e:
            _LOGGER.error("Error checking session validity: %s", e)
            return False

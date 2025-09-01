"""Session client for My Verisure API."""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, Optional

from .base_client import BaseClient
from .models.dto.session_dto import SessionDTO, DeviceIdentifiersDTO

_LOGGER = logging.getLogger(__name__)


class SessionClient(BaseClient):
    """Session client for My Verisure API."""

    def __init__(self, user: str, hash_token: Optional[str] = None, session_data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the session client."""
        super().__init__()
        self.user = user
        self._hash = hash_token
        self._session_data = session_data or {}

    def _get_session_file(self) -> str:
        """Get the path to the session file."""
        # Use the same directory as device files
        storage_dir = os.path.expanduser("~/.storage")
        if not os.path.exists(storage_dir):
            # Fallback to current directory
            storage_dir = "."

        return os.path.join(
            storage_dir, f"my_verisure_session_{self.user}.json"
        )

    async def save_session(
        self,
        session_data: Dict[str, Any],
        hash_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        device_identifiers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Save session data to file."""
        session_file_data = {
            "cookies": self._cookies,
            "session_data": session_data,
            "hash": hash_token,  # Keep for backward compatibility
            "user": self.user,
            "device_identifiers": device_identifiers,
            "saved_time": int(time.time()),
        }

        def _save_session_sync():
            # Ensure directory exists
            file_path = self._get_session_file()
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "w") as f:
                json.dump(session_file_data, f, indent=2)

        # Run the file operation in a thread to avoid blocking
        await asyncio.to_thread(_save_session_sync)

        _LOGGER.warning("Session saved to %s", self._get_session_file())
        _LOGGER.warning(
            "Saved session includes JWT token: %s",
            "Yes" if hash_token else "No",
        )
        if hash_token:
            _LOGGER.warning(
                "Saved JWT token length: %d characters", len(hash_token)
            )

        # Log tokens if available
        hash_hash = session_data.get("hash") if session_data else None
        refresh_hash = (
            session_data.get("refreshToken") if session_data else None
        )

        _LOGGER.warning(
            "Saved session includes hash token: %s",
            "Yes" if hash_hash else "No",
        )
        if hash_hash:
            _LOGGER.warning(
                "Saved hash token length: %d characters", len(hash_hash)
            )
            _LOGGER.warning(
                "Hash token preview: %s...",
                hash_hash[:20] if len(hash_hash) > 20 else hash_hash,
            )

        _LOGGER.warning(
            "Saved session includes refresh token: %s",
            "Yes" if refresh_hash else "No",
        )
        if refresh_hash:
            _LOGGER.warning(
                "Saved refresh token length: %d characters", len(refresh_hash)
            )
            _LOGGER.warning(
                "Refresh token preview: %s...",
                refresh_hash[:20] if len(refresh_hash) > 20 else refresh_hash,
            )

    async def load_session(self) -> Optional[Dict[str, Any]]:
        """Load session data from file."""

        def _load_session_sync():
            file_path = self._get_session_file()
            if not os.path.exists(file_path):
                return None

            try:
                with open(file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                _LOGGER.error("Failed to load session: %s", e)
                return None

        # Run the file operation in a thread to avoid blocking
        session_data = await asyncio.to_thread(_load_session_sync)

        if session_data is None:
            _LOGGER.debug(
                "No session file found at %s", self._get_session_file()
            )
            return None

        _LOGGER.warning("Loading: %s", self._get_session_file())
        _LOGGER.warning(json.dumps(session_data, indent=2, default=str))

        try:
            self._cookies = session_data.get("cookies", {})
            session_info = session_data.get("session_data", {})

            _LOGGER.warning("Session loaded from %s", self._get_session_file())
            _LOGGER.warning(
                "Loaded session includes JWT token: %s",
                "Yes" if session_data.get("hash") else "No",
            )

            # Log tokens if available
            hash_hash = session_info.get("hash") if session_info else None
            refresh_hash = (
                session_info.get("refreshToken") if session_info else None
            )

            _LOGGER.warning(
                "Loaded session includes hash token: %s",
                "Yes" if hash_hash else "No",
            )
            if hash_hash:
                _LOGGER.warning(
                    "Loaded hash token length: %d characters", len(hash_hash)
                )
                _LOGGER.warning(
                    "Hash token preview: %s...",
                    hash_hash[:20] if len(hash_hash) > 20 else hash_hash,
                )

            _LOGGER.warning(
                "Loaded session includes refresh token: %s",
                "Yes" if refresh_hash else "No",
            )
            if refresh_hash:
                _LOGGER.warning(
                    "Loaded refresh token length: %d characters",
                    len(refresh_hash),
                )
                _LOGGER.warning(
                    "Refresh token preview: %s...",
                    (
                        refresh_hash[:20]
                        if len(refresh_hash) > 20
                        else refresh_hash
                    ),
                )

            return session_data

        except Exception as e:
            _LOGGER.error("Failed to process session data: %s", e)
            return None

    def is_session_valid(
        self, session_data: Dict[str, Any], hash_token: Optional[str] = None
    ) -> bool:
        """Check if current session is still valid."""
        if not session_data:
            _LOGGER.warning("No session data available")
            return False

        if not hash_token:
            _LOGGER.warning("No authentication token available")
            return False

        # Check if session is not too old
        login_time = session_data.get("login_time", 0)
        current_time = int(time.time())
        session_age = current_time - login_time

        if session_age > 360:  # 6 minutes
            _LOGGER.warning("Session expired (age: %d seconds)", session_age)
            return False

        _LOGGER.warning(
            "Session appears valid (age: %d seconds, token present: %s)",
            session_age,
            "Yes" if hash_token else "No",
        )
        return True

    def get_session_dto(
        self,
        session_data: Dict[str, Any],
        hash_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        device_identifiers: Optional[Dict[str, Any]] = None,
    ) -> SessionDTO:
        """Convert session data to DTO."""
        return SessionDTO(
            cookies=self._cookies,
            session_data=session_data,
            hash=hash_token,
            user=self.user,
            device_identifiers=device_identifiers,
            saved_time=int(time.time()),
        )

    def get_device_identifiers_dto(
        self, device_identifiers: Dict[str, Any]
    ) -> DeviceIdentifiersDTO:
        """Convert device identifiers to DTO."""
        return DeviceIdentifiersDTO.from_dict(device_identifiers)

    def update_auth_token(self, hash_token: str, session_data: Dict[str, Any]) -> None:
        """Update the authentication token and session data."""
        self._hash = hash_token
        self._session_data = session_data
        _LOGGER.debug("Session client auth token updated")

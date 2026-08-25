"""Application policy for authenticated session state."""

from __future__ import annotations

import asyncio
from typing import Any

from .models.auth import AuthResult
from .exceptions import MyVerisurePersistenceError
from .ports import AuthenticatedSessionPort


class AuthSessionPersistence:
    """Build and persist entry-scoped credentials after authentication."""

    def __init__(self, session_manager: AuthenticatedSessionPort) -> None:
        self._session_manager = session_manager

    @staticmethod
    def _validate_refresh_token(value: Any) -> str | None:
        """Validate the optional provider refresh-token projection."""
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise MyVerisurePersistenceError("Authentication returned an invalid refresh token")
        return value

    async def persist(
        self,
        *,
        user: str,
        password: str,
        hash_token: str,
        refresh_token: str | None,
    ) -> tuple[str, str | None]:
        """Persist an already-normalized token pair."""
        if not isinstance(hash_token, str) or not hash_token.strip():
            raise MyVerisurePersistenceError("Authentication succeeded without a session hash")

        refresh_token = self._validate_refresh_token(refresh_token)
        try:
            await self._session_manager.async_update_credentials(
                user,
                password,
                hash_token,
                refresh_token,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise MyVerisurePersistenceError("Session persistence failed") from None
        self._session_manager.clear_service_blocked()
        return hash_token, refresh_token

    async def persist_result(
        self,
        result: AuthResult,
        *,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Persist a successful application authentication result."""
        if (
            not result.success
            or result.need_device_authorization is not False
            or not isinstance(result.hash, str)
            or not result.hash.strip()
        ):
            raise MyVerisurePersistenceError("Authentication succeeded without a session hash")

        username = self._session_manager.username if username is None else username
        password = self._session_manager.password if password is None else password
        if not username or password is None:
            raise MyVerisurePersistenceError("Authentication session has no credentials")

        refresh_token = self._validate_refresh_token(result.refresh_token)
        try:
            await self._session_manager.async_update_credentials(
                username,
                password,
                result.hash,
                refresh_token,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise MyVerisurePersistenceError("Session persistence failed") from None
        self._session_manager.clear_service_blocked()

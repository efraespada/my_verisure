"""Application policy for authenticated session state."""

from __future__ import annotations

from typing import Any

from ..session_manager import SessionManager


class AuthSessionPersistence:
    """Build and persist entry-scoped credentials after authentication."""

    def __init__(self, session_manager: SessionManager) -> None:
        self._session_manager = session_manager

    @staticmethod
    def build_session_data(user: str, login_data: dict[str, Any], login_time: int) -> dict[str, Any]:
        """Build the in-memory session projection from provider login data."""
        return {
            "user": user,
            "lang": login_data.get("lang", "ES"),
            "legals": login_data.get("legals", False),
            "changePassword": login_data.get("changePassword", False),
            "needDeviceAuthorization": login_data.get(
                "needDeviceAuthorization", False
            ),
            "login_time": login_time,
        }

    async def persist(
        self,
        *,
        user: str,
        password: str,
        login_data: dict[str, Any],
    ) -> tuple[str, str | None]:
        """Persist provider tokens and return the validated token pair."""
        hash_token = login_data.get("hash")
        if not hash_token:
            raise ValueError("Authentication succeeded without a session hash")

        refresh_token = login_data.get("refreshToken")
        await self._session_manager.async_update_credentials(
            user,
            password,
            hash_token,
            refresh_token,
        )
        self._session_manager.clear_service_blocked()
        return str(hash_token), refresh_token

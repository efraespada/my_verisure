"""Semantic application ports used by authentication workflows."""

from __future__ import annotations

from typing import Protocol


class AuthenticatedSessionPort(Protocol):
    """Port for storing and invalidating an authenticated session."""

    username: str | None
    password: str | None

    async def async_update_credentials(
        self,
        username: str,
        password: str,
        hash_token: str,
        refresh_token: str | None,
    ) -> None:
        """Persist the authenticated credentials for the current entry."""

    def clear_service_blocked(self) -> None:
        """Clear transient service-blocking state after successful auth."""

"""Authentication policy used by the coordinator update boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CoordinatorAuthenticationDecision:
    """Result of attempting authentication with an optional cache fallback."""

    authenticated: bool
    cached_data: dict[str, Any] | None = None


class CoordinatorAuthenticationPolicy:
    """Choose a live session or a previously persisted coordinator snapshot."""

    def __init__(
        self,
        login: Callable[[], Awaitable[bool]],
        load_cache: Callable[[], dict[str, Any]],
    ) -> None:
        self._login = login
        self._load_cache = load_cache

    async def authenticate(self) -> CoordinatorAuthenticationDecision:
        """Attempt login and return cached data only when login is unavailable."""
        if await self._login():
            return CoordinatorAuthenticationDecision(authenticated=True)

        cached_data = self._load_cache()
        if cached_data:
            return CoordinatorAuthenticationDecision(
                authenticated=False,
                cached_data=cached_data,
            )

        return CoordinatorAuthenticationDecision(authenticated=False)

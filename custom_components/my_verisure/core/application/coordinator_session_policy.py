"""Pure session state decisions used by the Home Assistant coordinator."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class SessionAction(StrEnum):
    """Action selected from the current entry-scoped session state."""

    USE_VALID_SESSION = "use_valid_session"
    SKIP_BLOCKED = "skip_blocked"
    REFRESH = "refresh"
    UNAVAILABLE = "unavailable"


class SessionStateReader(Protocol):
    """Port for reading session state."""

    is_authenticated: bool

    def is_session_valid(self) -> bool:
        """Return whether the session token is currently valid."""
        ...

    def is_service_blocked(self) -> bool:
        """Return whether provider backoff is active."""
        ...

    def can_attempt_refresh(self) -> bool:
        """Return whether credentials allow refresh."""
        ...


@dataclass(frozen=True)
class SessionDecision:
    """Decision and state snapshot for one coordinator login attempt."""

    action: SessionAction
    authenticated: bool
    valid: bool
    blocked: bool


class CoordinatorSessionPolicy:
    """Choose a session action without performing I/O or HA side effects."""

    def decide(self, session: SessionStateReader) -> SessionDecision:
        """Read session state once and choose the next coordinator action."""
        authenticated = session.is_authenticated
        valid = session.is_session_valid()
        blocked = session.is_service_blocked()

        if blocked:
            action = SessionAction.SKIP_BLOCKED
        elif authenticated and valid:
            action = SessionAction.USE_VALID_SESSION
        elif session.can_attempt_refresh():
            action = SessionAction.REFRESH
        else:
            action = SessionAction.UNAVAILABLE

        return SessionDecision(action, authenticated, valid, blocked)

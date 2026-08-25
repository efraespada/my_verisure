"""Pure mapping of provider failures at the Home Assistant update boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureServiceBlockedError,
)


class CoordinatorFailureKind(StrEnum):
    """Failure categories understood by the HA coordinator."""

    SERVICE_BLOCKED = "service_blocked"
    AUTHENTICATION = "authentication"
    CONNECTION = "connection"
    PROVIDER = "provider"
    UNEXPECTED = "unexpected"


@dataclass(frozen=True)
class CoordinatorFailure:
    """Normalized failure without HA side effects."""

    kind: CoordinatorFailureKind
    message: str
    original: Exception


class CoordinatorFailureClassifier:
    """Classify provider failures before the HA adapter applies its policy."""

    def classify(self, error: Exception) -> CoordinatorFailure:
        if isinstance(error, MyVerisureServiceBlockedError):
            kind = CoordinatorFailureKind.SERVICE_BLOCKED
        elif isinstance(error, MyVerisureAuthenticationError):
            kind = CoordinatorFailureKind.AUTHENTICATION
        elif isinstance(error, MyVerisureConnectionError):
            kind = CoordinatorFailureKind.CONNECTION
        elif isinstance(error, MyVerisureError):
            kind = CoordinatorFailureKind.PROVIDER
        else:
            kind = CoordinatorFailureKind.UNEXPECTED
        messages = {
            CoordinatorFailureKind.SERVICE_BLOCKED: "Service temporarily blocked",
            CoordinatorFailureKind.AUTHENTICATION: "Authentication required",
            CoordinatorFailureKind.CONNECTION: "Connection failed",
            CoordinatorFailureKind.PROVIDER: "Provider operation failed",
            CoordinatorFailureKind.UNEXPECTED: "Operation failed",
        }
        return CoordinatorFailure(
            kind=kind,
            message=messages[kind],
            original=error,
        )

"""Pure polling decisions for camera image requests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


REQUEST_ALREADY_EXISTS = "request_already_exists"
NO_RESPONSE_TO_REQUEST = "alarm-manager.error_no_response_to_request"
PROCESSING_MESSAGE = "alarm-manager.photo-request.processing"


class PollingAction(str, Enum):
    """Action the camera adapter must perform after a provider response."""

    RETRY = "retry"
    RETURN_FAILURE = "return_failure"
    COMPLETE = "complete"
    WAIT = "wait"
    RAISE = "raise"


@dataclass(frozen=True)
class PollingDecision:
    """Typed polling decision with an optional provider error."""

    action: PollingAction
    message: str | None = None


def decide_initial_request(error_message: str, attempt: int, max_attempts: int) -> PollingDecision:
    """Decide how to handle a failed initial image request."""
    if REQUEST_ALREADY_EXISTS in error_message:
        if attempt < max_attempts:
            return PollingDecision(PollingAction.RETRY, error_message)
        return PollingDecision(PollingAction.RETURN_FAILURE, error_message)
    return PollingDecision(PollingAction.RAISE, error_message)


def decide_status(
    status: str,
    message: str,
    attempt: int,
    max_attempts: int,
) -> PollingDecision:
    """Decide how to handle one image request status response."""
    if message == NO_RESPONSE_TO_REQUEST:
        return PollingDecision(PollingAction.RETURN_FAILURE, message)
    if status == "OK" and message != PROCESSING_MESSAGE:
        return PollingDecision(PollingAction.COMPLETE, message)
    if status == "KO":
        return PollingDecision(PollingAction.RETURN_FAILURE, message)
    if attempt < max_attempts:
        return PollingDecision(PollingAction.WAIT, message)
    return PollingDecision(PollingAction.RETURN_FAILURE, message)

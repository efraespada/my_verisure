"""Contract tests for camera request polling decisions."""

from custom_components.my_verisure.core.application.camera_request_polling import (
    NO_RESPONSE_TO_REQUEST,
    PROCESSING_MESSAGE,
    PollingAction,
    decide_initial_request,
    decide_status,
)


def test_existing_request_retries_before_limit_and_fails_at_limit() -> None:
    assert decide_initial_request("request_already_exists", 1, 3).action is PollingAction.RETRY
    assert decide_initial_request("request_already_exists", 3, 3).action is PollingAction.RETURN_FAILURE


def test_unknown_initial_error_is_raised_by_adapter() -> None:
    decision = decide_initial_request("provider unavailable", 1, 3)

    assert decision.action is PollingAction.RAISE
    assert decision.message == "provider unavailable"


def test_status_decisions_cover_completion_failure_and_wait() -> None:
    assert decide_status("OK", "completed", 1, 3).action is PollingAction.COMPLETE
    assert decide_status("KO", "failed", 1, 3).action is PollingAction.RETURN_FAILURE
    assert decide_status("OK", PROCESSING_MESSAGE, 1, 3).action is PollingAction.WAIT
    assert decide_status("OK", PROCESSING_MESSAGE, 3, 3).action is PollingAction.RETURN_FAILURE
    assert decide_status("OK", NO_RESPONSE_TO_REQUEST, 1, 3).action is PollingAction.RETURN_FAILURE

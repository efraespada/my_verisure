"""Tests for the coordinator session policy."""

from unittest.mock import Mock

import pytest

from custom_components.my_verisure.core.application.coordinator_session_policy import (
    CoordinatorSessionPolicy,
    SessionAction,
)


@pytest.mark.parametrize(
    ("authenticated", "valid", "blocked", "refreshable", "expected"),
    [
        (True, True, False, False, SessionAction.USE_VALID_SESSION),
        (True, False, True, True, SessionAction.SKIP_BLOCKED),
        (True, False, False, True, SessionAction.REFRESH),
        (False, False, False, False, SessionAction.UNAVAILABLE),
    ],
)
def test_decide_session_action(
    authenticated, valid, blocked, refreshable, expected
) -> None:
    session = Mock(
        is_authenticated=authenticated,
        is_session_valid=Mock(return_value=valid),
        is_service_blocked=Mock(return_value=blocked),
        can_attempt_refresh=Mock(return_value=refreshable),
    )

    decision = CoordinatorSessionPolicy().decide(session)

    assert decision.action is expected
    assert decision.authenticated is authenticated
    assert decision.valid is valid
    assert decision.blocked is blocked


def test_blocked_session_does_not_need_refresh_check() -> None:
    session = Mock(
        is_authenticated=False,
        is_session_valid=Mock(return_value=False),
        is_service_blocked=Mock(return_value=True),
        can_attempt_refresh=Mock(),
    )

    assert CoordinatorSessionPolicy().decide(session).action is SessionAction.SKIP_BLOCKED
    session.can_attempt_refresh.assert_not_called()

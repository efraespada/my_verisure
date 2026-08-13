"""Tests for coordinator failure classification."""

import pytest

from custom_components.my_verisure.core.api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureServiceBlockedError,
)
from custom_components.my_verisure.core.application.coordinator_failure import (
    CoordinatorFailureClassifier,
    CoordinatorFailureKind,
)


@pytest.mark.parametrize(
    ("error", "kind"),
    [
        (MyVerisureServiceBlockedError("blocked"), CoordinatorFailureKind.SERVICE_BLOCKED),
        (MyVerisureAuthenticationError("auth"), CoordinatorFailureKind.AUTHENTICATION),
        (MyVerisureConnectionError("offline"), CoordinatorFailureKind.CONNECTION),
        (MyVerisureError("provider"), CoordinatorFailureKind.PROVIDER),
        (RuntimeError("bug"), CoordinatorFailureKind.UNEXPECTED),
    ],
)
def test_classifier_preserves_error_and_assigns_kind(error, kind):
    failure = CoordinatorFailureClassifier().classify(error)

    assert failure.kind is kind
    assert failure.message == str(error)
    assert failure.original is error

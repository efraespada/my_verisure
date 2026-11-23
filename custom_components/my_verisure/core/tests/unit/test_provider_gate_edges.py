"""Untrusted Retry-After and operation-namespace admission boundaries.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import math

import pytest

from custom_components.my_verisure.core.api.provider_request_gate import (
    DEFAULT_BLOCKED_COOLDOWN_SECONDS,
    ProviderRequestGate,
    retry_after_seconds,
)


@pytest.mark.parametrize(
    "header",
    [
        "Mon, 23 Nov 2026 10:00:00",
        "Mon, 23 Nov 2026 10:00:00 -0000",
        "Mon, 23 Nov 10000 10:00:00 GMT",
        "Mon, 23 Nov 99999999999999999999 10:00:00 GMT",
    ],
)
def test_ambiguous_or_unrepresentable_http_date_uses_finite_default(header):
    """A missing timezone or impossible datetime cannot shorten the cooldown."""
    seconds = retry_after_seconds(header, 1800000000.0)
    assert seconds == DEFAULT_BLOCKED_COOLDOWN_SECONDS
    assert math.isfinite(seconds)


@pytest.mark.parametrize(
    "header",
    [
        "",
        " " * 128,
        "9" * 129,
        "４２",
        42,
        True,
        b"42",
    ],
)
def test_invalid_header_type_size_or_ascii_grammar_uses_default(header):
    assert retry_after_seconds(header, 1800000000.0) == (
        DEFAULT_BLOCKED_COOLDOWN_SECONDS
    )


def test_maximum_numeric_header_is_finite_and_whitespace_is_trimmed():
    assert retry_after_seconds(" 42 ", 1800000000.0) == 42.0
    seconds = retry_after_seconds("9" * 128, 1800000000.0)
    assert seconds > DEFAULT_BLOCKED_COOLDOWN_SECONDS
    assert math.isfinite(seconds)


@pytest.mark.parametrize("now", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_date_arithmetic_falls_back_to_finite_cooldown(now):
    assert retry_after_seconds("Mon, 23 Nov 2026 10:00:00 GMT", now) == (
        DEFAULT_BLOCKED_COOLDOWN_SECONDS
    )


@pytest.mark.parametrize("namespace", [None, 42, True, [], "", "x" * 2049])
def test_invalid_namespace_cannot_create_or_replace_shared_operation(namespace):
    gate = ProviderRequestGate()
    active = gate.get_operation_state("synthetic-active-operation")
    active.generation = 7
    for resolve in (gate.get_operation_state, gate.get_operation_lock):
        with pytest.raises(ValueError, match="bounded nonempty string"):
            resolve(namespace)
    assert gate.get_operation_state("synthetic-active-operation") is active
    assert active.generation == 7
    assert not active.lock.locked()


def test_maximum_operation_namespace_reuses_the_same_generation_and_locks():
    gate = ProviderRequestGate()
    namespace = "x" * 2048
    state = gate.get_operation_state(namespace)
    state.generation = 3
    assert gate.get_operation_state(namespace) is state
    assert gate.get_operation_lock(namespace) is state.lock
    assert gate.get_operation_state(namespace).generation == 3

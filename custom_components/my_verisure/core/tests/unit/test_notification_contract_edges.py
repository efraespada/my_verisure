"""Notification replay, privacy, time and asynchronous failure boundaries.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import json

import pytest

from custom_components.my_verisure.core.api.notification_mapper import (
    NotificationMapper,
)
from custom_components.my_verisure.core.application.notification_refresh import (
    BackgroundReadBudget,
    NotificationRefreshScheduler,
)
from custom_components.my_verisure.core.application.photo_notifications import (
    PhotoNotifications,
)

from .test_notification_admission import NOW, PRIVATE, envelope, make_hub
from .test_notification_refresh import Clock, notice, settle


@pytest.mark.parametrize("signal", [None, 123, "", "x" * 129, "not-numeric"])
def test_unsupported_private_signal_is_not_reinterpreted_or_published(signal):
    value = NotificationMapper("house", "entry")(
        envelope(idSignal=signal), "delivery", NOW
    )
    assert value.reason == "accepted"
    assert value.notice.signal_id is None
    assert "idSignal" not in value.notice.event.public_data()


@pytest.mark.parametrize("advanced", [None, "broken", "[]", [], {"requestId": 123}])
def test_invalid_optional_operation_metadata_preserves_safe_report_without_correlation(
    advanced,
):
    value = NotificationMapper("house", "entry")(
        envelope("ARMDISARM", advancedInfo=advanced),
        "delivery",
        NOW,
    )
    assert value.reason == "accepted"
    assert value.notice.operation_id is None
    assert PRIVATE not in json.dumps(value.notice.event.public_data())


def test_deep_optional_json_never_escapes_admission_or_exposes_its_contents():
    nesting = "[" * 2000 + "0" + "]" * 2000
    mapper = NotificationMapper("house", "entry")
    # Supported Python patch versions may reject deep JSON or parse it
    # iteratively. Either outcome must remain within the admission contract.
    raw = '{"request":"NOT","numinst":"house","private":' + nesting + "}"
    mapped = mapper({"data": {"text": raw}}, "deep", NOW)
    assert mapped.reason in {"accepted", "malformed"}
    if mapped.notice is not None:
        assert "private" not in mapped.notice.event.public_data()
    auxiliary = mapper(envelope("ARMDISARM", advancedInfo=nesting), "auxiliary", NOW)
    assert auxiliary.reason == "accepted"
    assert auxiliary.notice.operation_id is None


@pytest.mark.parametrize(
    "changes",
    [
        {"request": "lowercase"},
        {"numinst": "x" * 65},
        {"timeStamp": -1},
        {"timeStamp": "not-a-timestamp"},
    ],
)
def test_invalid_recipient_request_or_epoch_is_rejected(changes):
    mapped = NotificationMapper("house", "entry")(envelope(**changes), "delivery", NOW)
    assert mapped.reason == "malformed" and mapped.notice is None


def test_non_text_and_invalid_unicode_are_rejected_before_mapping():
    mapper = NotificationMapper("house", "entry")
    assert mapper({"data": {"text": {}}}, "object", NOW).reason == "malformed"
    assert mapper({"data": {"text": "\ud800"}}, "unicode", NOW).reason == "malformed"
    numeric = NotificationMapper("42", "entry")(envelope(numinst=42), "numeric", NOW)
    assert numeric.reason == "accepted" and numeric.notice.event.scope == "installation"


@pytest.mark.parametrize(
    "seconds,freshness", [(-300, "fresh"), (-301, "stale"), (60, "fresh")]
)
def test_occurrence_time_boundaries_preserve_source_time(seconds, freshness):
    mapped = NotificationMapper("house", "entry")(
        envelope(timeStamp=str(int((NOW + seconds) * 1000))),
        "delivery",
        NOW,
    )
    assert mapped.notice.event.occurred_at == NOW + seconds
    assert mapped.notice.event.freshness == freshness


@pytest.mark.parametrize(
    "facts,expected",
    [
        (
            {
                "internal_day": True,
                "internal_night": False,
                "internal_total": None,
                "external": True,
            },
            {
                "internal_day": True,
                "internal_night": False,
                "internal_total": None,
                "external": True,
            },
        ),
        ({"internal_day": "false", "external": 1}, {}),
        (
            {
                "image_count": 0,
                "incident_state": "open",
                "alarm_state": "D",
                "origin": "provider_notice",
            },
            {
                "image_count": 0,
                "incident_state": "open",
                "alarm_state": "D",
                "origin": "provider_notice",
            },
        ),
        (
            {
                "image_count": 8,
                "incident_state": "not_listed",
                "origin": "reconciliation",
            },
            {
                "image_count": 8,
                "incident_state": "not_listed",
                "origin": "reconciliation",
            },
        ),
        (
            {
                "image_count": 9,
                "incident_state": "closed",
                "alarm_state": PRIVATE,
                "origin": PRIVATE,
            },
            {},
        ),
    ],
)
def test_confirmed_public_facts_are_finite_typed_and_allowlisted(facts, expected):
    hub = make_hub()
    result = hub.publish_verified(
        "alarm_state_confirmed", facts={**facts, "body": PRIVATE}
    )
    assert dict(result.facts) == expected
    assert PRIVATE not in json.dumps(result.public_data())


@pytest.mark.parametrize(
    "timestamp", [True, -1, float("inf"), float("nan"), 1e30, "now"]
)
def test_invalid_verification_clock_is_rejected_without_mutating_history(timestamp):
    hub = make_hub()
    with pytest.raises(ValueError):
        hub.publish_verified("photo_ready", timestamp=timestamp)
    assert hub.diagnostics()["recent"] == []


def test_verification_metadata_uses_opaque_identity_and_safe_entity_references():
    hub = make_hub()
    valid = hub.publish_verified(
        "photo_ready",
        correlation_id="a" * 64,
        subject_entity_id="camera.front_door",
    )
    assert valid.correlation_id == "a" * 64
    assert valid.subject_entity_id == "camera.front_door"
    invalid = hub.publish_verified(
        "photo_ready",
        correlation_id=PRIVATE,
        subject_entity_id="camera." + PRIVATE,
    )
    assert invalid.subject_entity_id is None
    assert invalid.correlation_id != PRIVATE
    assert PRIVATE not in json.dumps(invalid.public_data())
    assert (
        hub.publish_verified("photo_ready").event_id
        != hub.publish_verified("photo_ready").event_id
    )
    with pytest.raises(ValueError):
        hub.publish_verified("photo_ready", delivery="invalid")
    with pytest.raises(ValueError):
        hub.publish_verified("photo_ready", verification="raw_payload")


@pytest.mark.parametrize("delivery", ["buffered", "restored", "reconciled"])
def test_non_live_verification_updates_observation_without_firing_automations(delivery):
    hub = make_hub()
    events = []
    hub.subscribe(events.append)
    hub.activate()
    result = hub.publish_verified("incident_status_confirmed", delivery=delivery)
    assert result is not None
    assert hub.diagnostics()["recent"][-1]["delivery"] == delivery
    assert not events


@pytest.mark.parametrize("version", [None, 0, 2, True, 1.0, "1"])
def test_unsupported_replay_versions_do_not_seed_delivery_history(version):
    hub = make_hub()
    hub.restore_replay({"version": version, "seen": [["a" * 64, NOW]]})
    assert hub.export_replay()["seen"] == []


def test_replay_restore_ignores_bad_shapes_and_nonfinite_out_of_window_stamps():
    hub = make_hub()
    hub.restore_replay({"version": 1, "seen": "invalid"})
    hub.restore_replay(
        {
            "version": 1,
            "seen": [
                None,
                ["short"],
                {"hash": "a" * 64, "time": NOW},
                ["a" * 64, True],
                ["b" * 64, float("nan")],
                ["c" * 64, NOW + 61],
                ["d" * 64, NOW - 86401],
                ["e" * 64, NOW],
            ],
        }
    )
    assert hub.export_replay()["seen"] == [["e" * 64, NOW]]


def test_replay_ttl_retains_boundary_then_expires_without_emitting_history():
    now = [NOW]
    hub = make_hub(clock=lambda: now[0])
    events = []
    hub.subscribe(events.append)
    hub.activate()
    hub.receive(envelope("NOT"), "delivery")
    now[0] += 86400
    hub.receive(envelope("NOT", timeStamp=int(now[0] * 1000)), "delivery")
    assert len(events) == 1
    now[0] += 1
    assert hub.export_replay()["seen"] == []
    hub.receive(envelope("NOT", timeStamp=int(now[0] * 1000)), "delivery")
    assert len(events) == 2


def test_legacy_resume_ids_keep_photo_scope_and_filter_invalid_values():
    photos = PhotoNotifications()
    hub = make_hub(photos=photos)
    hub.restore_ids(["valid", "", None, "x" * 513])
    assert hub.recent_ids == photos.recent_ids == ["valid"]
    hub.receive(envelope("NOT"), "valid")
    assert hub.diagnostics()["counters"]["duplicate"] == 1


def test_bad_delivery_and_foreign_recipient_update_safe_diagnostics_only():
    hub = make_hub()
    public, hints = [], []
    hub.subscribe(public.append)
    hub.subscribe_hints(hints.append)
    hub.activate()
    for identity in (None, "", "x" * 513):
        hub.receive(envelope("NOT"), identity)
    hub.receive(envelope("NOT", numinst="foreign-private-house"), "foreign")
    counters = hub.diagnostics()["counters"]
    assert counters["malformed"] == 3 and counters["foreign_scope"] == 1
    assert not public and not hints
    assert "foreign-private-house" not in json.dumps(hub.diagnostics())


def test_health_and_hint_failures_are_isolated_and_unsubscribe_is_idempotent():
    hub = make_hub()
    observed, hints = [], []

    def fail(*args):
        raise RuntimeError(PRIVATE)

    hub.subscribe_diagnostics(fail)
    hub.subscribe_hints(fail)
    remove = hub.subscribe_diagnostics(lambda: observed.append(hub.connected))
    hub.subscribe_hints(hints.append)
    hub.activate()
    hub.set_binding_state("bound")
    hub.connected = True
    assert hub.connected and observed[-1]
    hub.receive(envelope("ARMDISARM", timeStamp=None), "live")
    assert hints
    assert hub.diagnostics()["counters"]["consumer_failed"] >= 4
    assert PRIVATE not in json.dumps(hub.diagnostics())
    with pytest.raises(ValueError):
        hub.set_binding_state("raw-secret-state")
    remove()
    remove()
    hub.close()
    late = hub.subscribe(lambda value: observed.append(value))
    late()
    late()
    hub.receive(envelope("NOT"), "closed")
    assert hub.publish_verified("photo_ready") is None


def test_observation_switch_does_not_disable_independent_state_hint_consumers():
    hub = make_hub(observation_enabled=False)
    public, hints = [], []
    hub.subscribe(public.append)
    hub.subscribe_hints(hints.append)
    hub.activate()
    hub.receive(envelope("ARMDISARM"), "delivery")
    hub.publish_verified("alarm_state_confirmed", facts={"alarm_state": "D"})
    assert not public and len(hints) == 1


def test_unknown_codes_cannot_expand_public_coverage_or_history():
    hub = make_hub()
    for index in range(600):
        hub.receive(envelope(f"UNKNOWN_{index}"), f"private-delivery-{index}")
    diagnostics = hub.diagnostics()
    assert diagnostics["coverage"] == {"unclassified": 600}
    assert len(diagnostics["recent"]) == 100
    assert len(hub.export_replay()["seen"]) == 512
    assert len(hub.recent_ids) == 128
    assert "UNKNOWN_" not in json.dumps(diagnostics)
    assert "private-delivery-" not in json.dumps(diagnostics)


@pytest.mark.asyncio
async def test_initial_background_budget_does_not_depend_on_clock_reference():
    clock = Clock()
    clock.now = -100.0
    budget = BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep)
    await budget.acquire()
    assert clock.waits == []
    await budget.acquire()
    assert clock.waits == [30]


@pytest.mark.asyncio
async def test_incident_reference_schedules_one_authoritative_resource():
    clock, verified = Clock(), []

    async def verify(value):
        verified.append(value)
        return True

    scheduler = NotificationRefreshScheduler(
        verify,
        budget=BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep),
        state_enabled=True,
        sleep=clock.sleep,
    )
    scheduler.submit(notice("SMARTNOT", signal="321"))
    await settle(lambda: len(verified) == 1)
    assert verified[0].signal_id == "321"
    assert scheduler.diagnostics()["started"] == 1
    await scheduler.async_close()


@pytest.mark.asyncio
async def test_block_during_budget_wait_preserves_hint_without_reading():
    clock, verified, blocked = Clock(), [], [0.0]

    async def budget_sleep(seconds):
        await clock.sleep(seconds)
        blocked[0] = clock.now + 600

    async def verify(value):
        verified.append(clock.now)
        return True

    budget = BackgroundReadBudget(clock=lambda: clock.now, sleep=budget_sleep)
    await budget.acquire()
    scheduler = NotificationRefreshScheduler(
        verify,
        budget=budget,
        state_enabled=True,
        sleep=clock.sleep,
        blocked_for=lambda: max(0, blocked[0] - clock.now),
    )
    scheduler.submit(notice())
    await settle(lambda: bool(verified))
    assert verified == [630]
    assert scheduler.diagnostics()["started"] == 1
    await scheduler.async_close()


@pytest.mark.asyncio
async def test_newer_hint_arriving_during_deferred_read_wins_over_old_hint():
    clock, values = Clock(), []
    entered, release = asyncio.Event(), asyncio.Event()

    async def verify(value):
        values.append(value)
        if len(values) == 1:
            entered.set()
            await release.wait()
            return False
        return True

    scheduler = NotificationRefreshScheduler(
        verify,
        budget=BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep),
        state_enabled=True,
        sleep=clock.sleep,
    )
    first, newest = notice(delivery="old"), notice(delivery="new")
    scheduler.submit(first)
    await entered.wait()
    scheduler.submit(newest)
    release.set()
    await settle(lambda: len(values) == 2)
    assert values == [first, newest]
    assert scheduler.diagnostics()["deferred"] == 1
    await scheduler.async_close()


@pytest.mark.asyncio
async def test_scheduler_close_cancels_inflight_read_and_drops_remaining_work():
    clock = Clock()
    entered, cancelled = asyncio.Event(), asyncio.Event()

    async def verify(value):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    scheduler = NotificationRefreshScheduler(
        verify,
        budget=BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep),
        state_enabled=True,
        sleep=clock.sleep,
    )
    scheduler.submit(notice())
    await entered.wait()
    await scheduler.async_close()
    assert cancelled.is_set()
    assert scheduler.diagnostics()["pending"] == 0
    await scheduler.async_close()


def test_reconnect_suppresses_backlog_and_keeps_new_delivery():
    now = [NOW]
    hub = make_hub(clock=lambda: now[0])
    public, hints = [], []
    hub.subscribe(public.append)
    hub.subscribe_hints(hints.append)
    hub.connected = True
    hub.activate()
    hub.connected = False
    now[0] += 10
    hub.connected = True
    assert len(hints) == 1
    assert hints[0].event.delivery == "reconciled"
    assert hints[0].event.kind == "alarm_operation_reported"
    assert hints[0].event.provider_request is None
    assert not public and hub.diagnostics()["last_received"] is None
    for index, stamp in enumerate((NOW + 5, NOW + 10)):
        hub.receive(
            envelope("ARMDISARM", timeStamp=int(stamp * 1000)), f"queued-{index}"
        )
    assert not public and len(hints) == 1
    assert hub.diagnostics()["counters"]["reconciled"] == 2
    assert all(
        value["delivery"] == "reconciled" for value in hub.diagnostics()["recent"]
    )
    now[0] += 1
    hub.receive(envelope("ARMDISARM", timeStamp=int(now[0] * 1000)), "genuinely-new")
    assert len(public) == 1 and public[0].delivery == "live"
    assert len(hints) == 2 and hints[-1].event.delivery == "live"


@pytest.mark.asyncio
async def test_recovery_hint_only_seeds_state_when_enabled_without_automation_replay():
    clock = Clock()
    clock.now = NOW
    hub = make_hub(clock=lambda: clock.now)
    public, hints, reads = [], [], []
    hub.subscribe(public.append)
    hub.subscribe_hints(hints.append)
    hub.connected = True
    hub.activate()
    hub.connected = False
    clock.now += 5
    hub.connected = True
    assert len(hints) == 1

    async def verify(value):
        reads.append(value)
        hub.publish_verified(
            "alarm_state_confirmed",
            delivery="reconciled",
            facts={"alarm_state": "D"},
        )
        return True

    budget = BackgroundReadBudget(clock=lambda: clock.now, sleep=clock.sleep)
    off = NotificationRefreshScheduler(verify, budget=budget, sleep=clock.sleep)
    off.submit(hints[0])
    assert off.diagnostics()["pending"] == 0
    assert not reads
    on = NotificationRefreshScheduler(
        verify,
        budget=budget,
        sleep=clock.sleep,
        state_enabled=True,
    )
    on.submit(hints[0])
    await settle(lambda: len(reads) == 1)
    assert not public
    assert hub.diagnostics()["recent"][-1]["delivery"] == "reconciled"
    assert hub.diagnostics()["recent"][-1]["alarm_state"] == "D"
    await on.async_close()
    await off.async_close()

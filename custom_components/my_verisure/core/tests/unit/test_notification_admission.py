"""Provider notice scope, privacy, replay and lifecycle contracts.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json
from unittest.mock import Mock

import pytest

from custom_components.my_verisure.core.api.notification_mapper import (
    NotificationMapper,
)
from custom_components.my_verisure.core.application.notifications import NotificationHub
from custom_components.my_verisure.core.application.photo_notifications import (
    PhotoNotifications,
)

NOW = 1_800_000_000.0
PRIVATE = "PRIVATE_PAYLOAD_DO_NOT_PUBLISH"


def envelope(request="INF", **overrides):
    event = {
        "request": request,
        "type": 0,
        "numinst": "house",
        "timeStamp": int(NOW * 1000),
        "idSignal": "123",
        "title": PRIVATE,
        "text": {"body": PRIVATE},
        "advancedInfo": json.dumps({"codeResponse": "OK", "requestId": PRIVATE}),
    }
    event.update(overrides)
    return {"data": {"text": json.dumps(event)}}


def make_hub(clock=lambda: NOW, **kwargs):
    return NotificationHub(
        "entry", NotificationMapper("house", "entry"), clock=clock, **kwargs
    )


@pytest.mark.parametrize(
    "provider_request,kind",
    [
        ("INF", "photo_reported"),
        ("ARMDISARM", "alarm_operation_reported"),
        ("ALARMCONNECT", "alarm_operation_reported"),
        ("ALARMDISCONNECT", "alarm_operation_reported"),
        ("ALARMSTATUS", "alarm_operation_reported"),
        ("SMARTNOT", "security_incident_reported"),
        ("ALARMTRIGGER", "security_incident_reported"),
        ("ALARMTRIPCANCELED", "security_incident_reported"),
        ("SCHCD", "arm_reminder"),
        ("UNPROTECTED", "unprotected_home"),
        ("SMARTDISARM", "smart_disarm_notice"),
        ("DIY", "device_maintenance_notice"),
        ("DIYKEYS", "device_maintenance_notice"),
        ("DIYREMINDER", "device_maintenance_notice"),
        ("DIYTRACKING", "device_maintenance_notice"),
        ("BATTERYSTATUS", "device_maintenance_notice"),
        ("PREDIY", "device_maintenance_notice"),
        ("PREDIYREMINDER", "device_maintenance_notice"),
        ("DIYTAMPER_DIY", "device_tamper_reported"),
        ("DIYTAMPER_NO_DIY", "device_tamper_reported"),
        ("MAINTENANCE", "maintenance_appointment"),
        ("MAINTENANCES", "maintenance_appointment"),
        ("RSCHAFTERSUSPEND", "maintenance_appointment"),
        ("ANSWER", "support_reply"),
        ("CHATHELP", "support_reply"),
        ("SUPPORTHUB", "support_reply"),
        ("NOT", "generic_notice"),
        ("PWC", "generic_notice"),
        ("AUTH", "account_notice"),
        ("AUTHTESTMODE", "account_notice"),
        ("TRUSTEDDEVICES", "account_notice"),
        ("RESETPASSW", "account_notice"),
        ("ACTIONPLAN", "account_notice"),
        ("CODEWORDS", "account_notice"),
        ("ALARMCHANGEUSER", "account_notice"),
        ("BILLINGDATA", "account_notice"),
        ("CONTRACT", "account_notice"),
        ("FIRST_INVOICE", "account_notice"),
        ("INVOICES", "account_notice"),
        ("KEYSREMOTE", "account_notice"),
        ("DEVICESFAST", "generic_notice"),
        ("DEVICESMOONSHOT", "generic_notice"),
        ("ENTRYEXITTIME", "generic_notice"),
        ("HOME", "generic_notice"),
        ("HOMEMOVE", "generic_notice"),
        ("IND", "generic_notice"),
        ("NOACCESSBROKER", "generic_notice"),
        ("NOINTERNET", "generic_notice"),
        ("SENTINELCONFIG", "generic_notice"),
        ("WIFI", "generic_notice"),
        ("WIFISETTINGS", "generic_notice"),
        ("FAMILIES", "account_notice"),
        ("INVITATIONACCEPTED", "account_notice"),
    ],
)
def test_declared_notice_families_are_reported_without_copying_content(
    provider_request, kind
):
    result = NotificationMapper("house", "entry")(
        envelope(provider_request), "delivery", NOW
    )
    assert result.reason == "accepted"
    notice = result.notice
    assert notice.event.kind == kind
    assert notice.event.stage == "reported"
    public = notice.event.public_data()
    assert public["provider_request"] == provider_request
    assert PRIVATE not in json.dumps(public)
    assert "numinst" not in public and "idSignal" not in public


@pytest.mark.parametrize(
    "payload,reason",
    [
        ({}, "malformed"),
        ({"data": {"text": "[]"}}, "malformed"),
        ({"data": {"text": "broken"}}, "malformed"),
        ({"data": {"text": "x" * 8193}}, "oversized"),
        (envelope(numinst="other"), "foreign_scope"),
        (envelope(numinst=True), "malformed"),
        (envelope(request=None), "malformed"),
        (envelope(timeStamp=True), "malformed"),
        (envelope(timeStamp=float("inf")), "malformed"),
        (envelope(timeStamp=int((NOW + 61) * 1000)), "future"),
    ],
)
def test_bad_or_foreign_input_does_not_enter_a_house_stream(payload, reason):
    result = NotificationMapper("house", "entry")(payload, "delivery", NOW)
    assert result.notice is None and result.reason == reason


def test_private_signal_fields_are_family_specific_and_id_is_entry_scoped():
    mapper = NotificationMapper("house", "entry")
    photo = mapper(envelope(), "delivery", NOW).notice
    arm = mapper(envelope("ARMDISARM"), "delivery", NOW).notice
    assert photo.signal_id == "123" and photo.photo_type == 0
    assert arm.operation_id == PRIVATE
    assert arm.signal_id is None
    other = NotificationMapper("house", "another-entry")(
        envelope(), "delivery", NOW
    ).notice
    assert other.event.event_id != photo.event.event_id


def test_shared_admission_deduplicates_before_independent_consumers():
    hub = make_hub()
    public, hints = [], []
    hub.subscribe(public.append)
    hub.subscribe_hints(hints.append)
    hub.activate()
    hub.receive(envelope(), "delivery")
    hub.receive(envelope(), "delivery")
    assert len(public) == len(hints) == 1
    assert hub.diagnostics()["counters"]["duplicate"] == 1


@pytest.mark.asyncio
async def test_pending_photo_wakeup_survives_disabled_observation_and_broken_listener(
    monkeypatch,
):
    from types import SimpleNamespace

    monkeypatch.setattr(
        "custom_components.my_verisure.core.application.photo_notifications.time",
        SimpleNamespace(time=lambda: NOW),
    )
    photos = PhotoNotifications()
    hub = make_hub(photos=photos, observation_enabled=False)
    hub.connected = True
    photos.begin("house", NOW)
    hub.subscribe(Mock(side_effect=RuntimeError(PRIVATE)))
    hub.receive(envelope(), "delivery")
    assert await photos.wait(0.01) == "123"
    hub.close()
    assert not photos.connected


def test_startup_buffer_is_bounded_and_does_not_replay_live_events():
    hub = make_hub()
    public = []
    hub.subscribe(public.append)
    for i in range(70):
        hub.receive(envelope("NOT"), f"delivery-{i}")
    assert not public
    assert hub.diagnostics()["counters"]["buffer_dropped"] == 6
    hub.activate()
    assert not public
    assert all(item["delivery"] == "buffered" for item in hub.diagnostics()["recent"])
    hub.receive(envelope("NOT"), "fresh")
    assert len(public) == 1 and public[0].delivery == "live"


def test_stale_unknown_and_unassigned_messages_are_observable_without_refresh_work():
    hub = make_hub()
    public, hints = [], []
    hub.subscribe(public.append)
    hub.subscribe_hints(hints.append)
    hub.activate()
    hub.receive(envelope("FUTURE_PROVIDER_KIND"), "unknown")
    hub.receive(envelope("ARMDISARM", timeStamp=int((NOW - 301) * 1000)), "stale")
    hub.receive(envelope("FAMILIES"), "personal")
    hub.receive(envelope("AUTH", numinst=None), "account")
    assert len(public) == 1 and public[0].kind == "unclassified_notice"
    assert public[0].provider_request is None
    assert not hints
    assert len(hub.diagnostics()["recent"]) == 4
    assert hub.diagnostics()["counters"]["unassigned"] == 2


def test_unknown_occurrence_time_is_not_replaced_with_receive_time():
    notice = NotificationMapper("house", "entry")(
        envelope("ARMDISARM", timeStamp=None), "id", NOW
    ).notice
    assert notice.event.occurred_at is None and notice.event.freshness == "unknown"


def test_replay_state_is_bounded_private_and_survives_reload_without_reemission():
    hub = make_hub()
    hub.activate()
    for i in range(520):
        hub.receive(envelope("NOT"), f"private-provider-id-{i}")
    state = hub.export_replay()
    assert len(state["seen"]) == 512
    assert "private-provider-id" not in json.dumps(state)
    restored = make_hub()
    restored.restore_replay(state)
    restored.restore_ids(hub.recent_ids)
    events = []
    restored.subscribe(events.append)
    restored.activate()
    restored.receive(envelope("NOT"), "private-provider-id-519")
    assert not events and restored.diagnostics()["counters"]["duplicate"] == 1


def test_verification_is_allowlisted_deduplicated_and_preserves_stage():
    hub = make_hub()
    events = []
    hub.subscribe(events.append)
    hub.activate()
    result = hub.publish_verified(
        "photo_ready",
        correlation_id="correlation",
        facts={"image_count": 3, "body": PRIVATE},
    )
    assert result.stage == "confirmed"
    assert result.public_data()["image_count"] == 3
    assert PRIVATE not in json.dumps(result.public_data())
    assert (
        hub.publish_verified(
            "photo_ready", correlation_id="correlation", facts={"image_count": 3}
        )
        is None
    )
    with pytest.raises(ValueError):
        hub.publish_verified("arbitrary")
    assert len(events) == 1


def test_subscriber_failure_unsubscribe_and_closed_receiver_are_isolated():
    hub = make_hub()
    hub.subscribe(Mock(side_effect=ValueError(PRIVATE)))
    other = []
    remove = hub.subscribe(other.append)
    hub.activate()
    hub.receive(envelope("NOT"), "first")
    assert len(other) == 1 and hub.diagnostics()["counters"]["consumer_failed"] == 1
    remove()
    hub.close()
    hub.receive(envelope("NOT"), "after-close")
    assert hub.publish_verified("photo_ready") is None
    assert len(other) == 1


def test_untyped_fact_values_are_ignored_without_breaking_event_delivery():
    hub = make_hub()
    result = hub.publish_verified(
        "photo_ready", facts={"origin": {}, "alarm_state": [], "image_count": True}
    )
    assert "origin" not in result.public_data()
    assert "alarm_state" not in result.public_data()
    assert "image_count" not in result.public_data()

"""Confirm notification facts only through fresh, scoped read-only results.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.notification_verification import (
    NotificationReadDeferred,
    NotificationReadUnavailable,
    NotificationVerifier,
    VerifiedPhoto,
)
from custom_components.my_verisure.core.application.notifications import NotificationHub
from custom_components.my_verisure.core.api.notification_mapper import (
    NotificationMapper,
)


def notice(kind="alarm_operation_reported", **changes):
    event = SimpleNamespace(
        kind=kind,
        correlation_id="synthetic-correlation",
        scope="installation",
        delivery="live",
        freshness="fresh",
        occurred_at=1000.0,
    )
    value = SimpleNamespace(
        event=event, signal_id="123", operation_id="synthetic-operation", photo_type=0
    )
    for key, new in changes.items():
        if hasattr(event, key):
            setattr(event, key, new)
        else:
            setattr(value, key, new)
    return cast(Any, value)


def state(external=False, *, night=False):
    return {
        "alarm_status": {
            "success": True,
            "data": {
                "internal": {
                    "day": {"status": False},
                    "night": {"status": night},
                    "total": {"status": False},
                },
                "external": {"status": external},
            },
        }
    }


async def test_state_change_publishes_once_after_seed_and_no_change_is_quiet():
    hub = Mock()
    reader = AsyncMock(return_value=state(True))
    consumer = NotificationVerifier(hub, read_state=reader)
    assert consumer.seed_state(state())
    assert await consumer.verify(notice())
    assert await consumer.verify(notice())
    hub.publish_verified.assert_called_once_with(
        "alarm_state_confirmed",
        correlation_id="synthetic-correlation",
        facts={
            "internal_day": False,
            "internal_night": False,
            "internal_total": False,
            "external": True,
            "alarm_state": "E",
        },
    )


@pytest.mark.parametrize("local", [False, True])
async def test_first_authoritative_baseline_only_emits_for_trusted_local_operation(
    local,
):
    hub = Mock()
    consumer = NotificationVerifier(
        hub,
        read_state=AsyncMock(return_value=state()),
        is_local_operation=lambda n: local,
    )
    assert await consumer.verify(notice())
    assert hub.publish_verified.call_count == int(local)


async def test_superseded_state_returns_pending_without_altering_baseline():
    hub = Mock()
    reader = AsyncMock(side_effect=[None, state(True)])
    consumer = NotificationVerifier(hub, read_state=reader)
    consumer.seed_state(state())
    assert await consumer.verify(notice()) is False
    assert await consumer.verify(notice()) is True
    assert hub.publish_verified.call_count == 1


async def test_unknown_state_is_not_a_confirmed_change():
    hub = Mock()
    consumer = NotificationVerifier(
        hub, read_state=AsyncMock(return_value={"alarm_status": {"data": {}}})
    )
    consumer.seed_state(state())
    assert await consumer.verify(notice())
    hub.publish_verified.assert_not_called()


async def test_missing_incident_permission_is_consumed_without_provider_query():
    hub, reader = Mock(), AsyncMock()
    consumer = NotificationVerifier(
        hub, read_incidents=reader, incident_permission=lambda: False
    )
    assert await consumer.verify(notice("security_incident_reported"))
    reader.assert_not_awaited()
    hub.publish_verified.assert_not_called()


async def test_explicit_incident_confirms_open_then_not_listed_never_closed():
    hub = Mock()
    reader = AsyncMock(side_effect=[("123",), ("123",), ()])
    consumer = NotificationVerifier(
        hub, read_incidents=reader, incident_permission=lambda: True
    )
    for _ in range(3):
        assert await consumer.verify(notice("security_incident_reported"))
    assert [call.kwargs["facts"] for call in hub.publish_verified.call_args_list] == [
        {"incident_state": "open"},
        {"incident_state": "not_listed"},
    ]
    assert all(
        call.kwargs["correlation_id"] == "synthetic-correlation"
        for call in hub.publish_verified.call_args_list
    )


async def test_superseded_incident_read_stays_pending():
    hub = Mock()
    consumer = NotificationVerifier(
        hub,
        read_incidents=AsyncMock(return_value=None),
        incident_permission=lambda: True,
    )
    assert await consumer.verify(notice("security_incident_reported")) is False
    hub.publish_verified.assert_not_called()


async def test_incident_without_private_reference_cannot_be_confirmed():
    hub, reader = Mock(), AsyncMock()
    consumer = NotificationVerifier(
        hub, read_incidents=reader, incident_permission=lambda: True
    )
    assert await consumer.verify(notice("security_incident_reported", signal_id=None))
    reader.assert_not_awaited()
    hub.publish_verified.assert_not_called()


async def test_photo_is_emitted_once_and_duplicate_signal_does_not_fetch_again():
    hub = Mock()
    reader = AsyncMock(return_value=VerifiedPhoto("camera.synthetic", 3))
    consumer = NotificationVerifier(hub, read_photo=reader)
    assert await consumer.verify(notice("photo_reported"))
    assert await consumer.verify(notice("photo_reported"))
    reader.assert_awaited_once()
    hub.publish_verified.assert_called_once_with(
        "photo_ready",
        correlation_id="synthetic-correlation",
        subject_entity_id="camera.synthetic",
        facts={"image_count": 3, "origin": "provider_notice"},
        verification="image_commit",
        deduplication_key="photo:camera.synthetic:123",
    )


async def test_rejected_photo_is_consumed_without_permanent_retries():
    hub = Mock()
    consumer = NotificationVerifier(hub, read_photo=AsyncMock(return_value=None))
    assert await consumer.verify(notice("photo_reported")) is True
    hub.publish_verified.assert_not_called()


async def test_busy_photo_can_be_explicitly_deferred():
    hub = Mock()
    consumer = NotificationVerifier(
        hub, read_photo=AsyncMock(side_effect=NotificationReadDeferred)
    )
    assert await consumer.verify(notice("photo_reported")) is False
    hub.publish_verified.assert_not_called()


@pytest.mark.parametrize(
    "change",
    [
        {"photo_type": 1},
        {"occurred_at": None},
        {"freshness": "unknown"},
        {"signal_id": None},
    ],
)
async def test_unverified_photo_metadata_does_not_request_images(change):
    hub, reader = Mock(), AsyncMock()
    consumer = NotificationVerifier(hub, read_photo=reader)
    assert await consumer.verify(notice("photo_reported", **change))
    reader.assert_not_awaited()


@pytest.mark.parametrize(
    "change",
    [
        {"scope": "account"},
        {"scope": "personal"},
        {"delivery": "buffered"},
        {"delivery": "restored"},
        {"delivery": "reconciled"},
        {"freshness": "stale"},
    ],
)
async def test_observational_notices_never_start_verification(change):
    hub, reader = Mock(), AsyncMock()
    consumer = NotificationVerifier(hub, read_state=reader)
    consumer.seed_state(state())
    assert await consumer.verify(notice(**change))
    reader.assert_not_awaited()
    hub.publish_verified.assert_not_called()


async def test_missing_occurrence_can_coarsely_reconcile_known_state():
    hub = Mock()
    consumer = NotificationVerifier(hub, read_state=AsyncMock(return_value=state(True)))
    consumer.seed_state(state())
    assert await consumer.verify(
        notice("unprotected_home", occurred_at=None, freshness="unknown")
    )
    hub.publish_verified.assert_called_once()


async def test_unknown_category_is_observed_without_any_provider_read():
    hub, reader = Mock(), AsyncMock()
    consumer = NotificationVerifier(
        hub,
        read_state=reader,
        read_incidents=reader,
        read_photo=reader,
        incident_permission=lambda: True,
    )
    assert await consumer.verify(notice("unclassified_notice"))
    reader.assert_not_awaited()
    hub.publish_verified.assert_not_called()


async def test_known_local_command_publishes_once_and_later_notice_reuses_baseline():
    hub, reader = Mock(), AsyncMock(return_value=state(True))
    consumer = NotificationVerifier(hub, read_state=reader)
    assert consumer.confirm_local_state(
        state(True), correlation_id="private-operation-reference"
    )
    reader.assert_not_awaited()
    hub.publish_verified.assert_called_once_with(
        "alarm_state_confirmed",
        correlation_id="private-operation-reference",
        verification="command_result",
        facts={
            "internal_day": False,
            "internal_night": False,
            "internal_total": False,
            "external": True,
            "alarm_state": "E",
            "origin": "local_request",
        },
    )
    assert await consumer.verify(notice())
    reader.assert_awaited_once()
    assert hub.publish_verified.call_count == 1


@pytest.mark.parametrize(
    "snapshot",
    [
        None,
        {},
        {"alarm_status": {"success": False, "data": state()["alarm_status"]["data"]}},
        {"alarm_status": {"success": True, "data": {}}},
        {
            "alarm_status": {
                "success": True,
                "data": {
                    "internal": {
                        "day": {"status": False},
                        "night": {"status": False},
                        "total": {"status": True},
                    },
                    "external": {"status": True},
                },
            }
        },
    ],
)
def test_unknown_or_unmapped_local_command_cannot_emit_confirmed_state(snapshot):
    hub = Mock()
    assert NotificationVerifier(hub).confirm_local_state(snapshot) is False
    hub.publish_verified.assert_not_called()


@pytest.mark.parametrize(
    "kind,reader_name",
    [
        ("alarm_operation_reported", "read_state"),
        ("security_incident_reported", "read_incidents"),
        ("photo_reported", "read_photo"),
    ],
)
async def test_definitively_unavailable_read_is_consumed_without_facts(
    kind, reader_name
):
    hub, reader = Mock(), AsyncMock(side_effect=NotificationReadUnavailable)
    consumer = NotificationVerifier(
        hub, **{reader_name: reader}, incident_permission=lambda: True
    )
    assert await consumer.verify(notice(kind)) is True
    reader.assert_awaited_once()
    hub.publish_verified.assert_not_called()


@pytest.mark.parametrize(
    "kind", ["alarm_operation_reported", "security_incident_reported", "photo_reported"]
)
async def test_disabled_read_ports_never_create_confirmed_facts(kind):
    hub = Mock()
    assert await NotificationVerifier(hub, incident_permission=lambda: True).verify(
        notice(kind)
    )
    hub.publish_verified.assert_not_called()


@pytest.mark.parametrize(
    "photo",
    [
        VerifiedPhoto("sensor.synthetic", 3),
        VerifiedPhoto("camera.synthetic", 0),
        VerifiedPhoto("camera.synthetic", 9),
        VerifiedPhoto("camera.synthetic", True),
    ],
)
def test_invalid_persisted_photo_result_never_creates_a_ready_event(photo):
    hub = Mock()
    assert not NotificationVerifier(hub).publish_photo(photo, signal_id="123")
    hub.publish_verified.assert_not_called()


def test_photo_origin_is_bounded_and_untrusted_origin_cannot_be_public():
    hub = Mock()
    assert NotificationVerifier(hub).publish_photo(
        VerifiedPhoto("camera.synthetic", 3), origin="private-raw-source"
    )
    assert hub.publish_verified.call_args.kwargs["facts"] == {
        "image_count": 3,
        "origin": "unknown",
    }


async def test_incident_cache_is_bounded_and_evicted_reference_can_return():
    hub = Mock()
    consumer = NotificationVerifier(
        hub, read_incidents=AsyncMock(return_value=()), incident_permission=lambda: True
    )
    for index in range(129):
        assert await consumer.verify(
            notice("security_incident_reported", signal_id=str(index))
        )
    assert len(consumer._incidents) == 128
    assert await consumer.verify(notice("security_incident_reported", signal_id="0"))
    assert hub.publish_verified.call_count == 130


def test_photo_cache_is_bounded_and_evicted_capture_can_return():
    hub = Mock()
    consumer = NotificationVerifier(hub)
    photo = VerifiedPhoto("camera.synthetic", 3)
    for index in range(129):
        assert consumer.publish_photo(photo, signal_id=str(index))
    assert len(consumer._photos) == 128
    assert consumer.publish_photo(photo, signal_id="0")
    assert hub.publish_verified.call_count == 130


@pytest.mark.parametrize("mode", ["day", "night", "total", "external"])
async def test_missing_zone_never_confirms_a_partially_known_state(mode):
    snapshot = state(True)
    data = snapshot["alarm_status"]["data"]
    section = data["external"] if mode == "external" else data["internal"][mode]
    section["status"] = None
    hub = Mock()
    consumer = NotificationVerifier(hub, read_state=AsyncMock(return_value=snapshot))
    consumer.seed_state(state())
    assert await consumer.verify(notice())
    assert not consumer.confirm_local_state(snapshot)
    hub.publish_verified.assert_not_called()


async def test_zone_combination_does_not_invent_unsupported_panel_codes():
    snapshot = state()
    snapshot["alarm_status"]["data"]["internal"]["day"]["status"] = True
    hub = Mock()
    consumer = NotificationVerifier(hub, read_state=AsyncMock(return_value=snapshot))
    consumer.seed_state(state())
    assert await consumer.verify(notice())
    assert hub.publish_verified.call_args.kwargs["facts"] == {
        "internal_day": True,
        "internal_night": False,
        "internal_total": False,
        "external": False,
    }


def test_same_photo_signal_from_local_capture_and_external_notice_is_not_republished():
    hub = Mock()
    consumer = NotificationVerifier(hub)
    photo = VerifiedPhoto("camera.synthetic", 3)
    assert consumer.publish_photo(photo, signal_id="123", origin="local_request")
    assert not consumer.publish_photo(photo, signal_id="123", origin="provider_notice")
    hub.publish_verified.assert_called_once()


async def test_photo_replay_prevents_duplicate_with_new_delivery():
    photo = VerifiedPhoto("camera.synthetic", 3)
    first_hub = NotificationHub(
        "synthetic-entry",
        NotificationMapper("synthetic-house", "synthetic-entry"),
        clock=lambda: 1000.0,
    )
    first_events = []
    first_hub.subscribe(first_events.append)
    first_hub.activate()
    first = NotificationVerifier(first_hub)
    assert first.publish_photo(
        photo, signal_id="123", correlation_id="first-delivery", origin="local_request"
    )
    replay = first_hub.export_replay()
    first_hub.close()
    restored_hub = NotificationHub(
        "synthetic-entry",
        NotificationMapper("synthetic-house", "synthetic-entry"),
        clock=lambda: 1001.0,
    )
    restored_events = []
    restored_hub.restore_replay(replay)
    restored_hub.subscribe(restored_events.append)
    restored_hub.activate()
    reader = AsyncMock(return_value=photo)
    restored = NotificationVerifier(restored_hub, read_photo=reader)
    assert not restored.publish_photo(
        photo,
        signal_id="123",
        correlation_id="different-delivery",
        origin="provider_notice",
    )
    assert await restored.verify(notice("photo_reported")) is True
    reader.assert_not_awaited()
    assert len(first_events) == 1 and not restored_events
    assert "photo:camera.synthetic:123" not in str(replay)
    restored_hub.close()


async def test_incident_replay_restores_missing_memory_and_records_reads():
    hub = Mock()
    replay = Mock()
    replay.get_resource_state.return_value = "open"
    reader = AsyncMock(side_effect=[("123",), (), ("123",)])
    consumer = NotificationVerifier(
        hub, read_incidents=reader, incident_permission=lambda: True, replay=replay
    )
    for index in range(3):
        assert await consumer.verify(
            notice("security_incident_reported", correlation_id=f"delivery-{index}")
        )
    replay.get_resource_state.assert_called_once_with("incident:123")
    assert [call.args for call in replay.set_resource_state.call_args_list] == [
        ("incident:123", "open"),
        ("incident:123", "not_listed"),
        ("incident:123", "open"),
    ]
    assert [call.kwargs["facts"] for call in hub.publish_verified.call_args_list] == [
        {"incident_state": "not_listed"},
        {"incident_state": "open"},
    ]


async def test_incident_state_survives_restart_and_reopening_is_a_new_transition():
    first_hub = NotificationHub(
        "synthetic-entry",
        NotificationMapper("synthetic-house", "synthetic-entry"),
        clock=lambda: 1000.0,
    )
    first_events = []
    first_hub.subscribe(first_events.append)
    first_hub.activate()
    first = NotificationVerifier(
        first_hub,
        read_incidents=AsyncMock(return_value=("123",)),
        incident_permission=lambda: True,
        replay=first_hub,
    )
    assert await first.verify(
        notice("security_incident_reported", correlation_id="first-delivery")
    )
    assert [dict(event.facts) for event in first_events] == [{"incident_state": "open"}]
    durable = first_hub.export_replay()
    first_hub.close()
    restored_hub = NotificationHub(
        "synthetic-entry",
        NotificationMapper("synthetic-house", "synthetic-entry"),
        clock=lambda: 1001.0,
    )
    restored_hub.restore_replay(durable)
    restored_events = []
    restored_hub.subscribe(restored_events.append)
    restored_hub.activate()
    restored = NotificationVerifier(
        restored_hub,
        read_incidents=AsyncMock(side_effect=[("123",), (), ("123",)]),
        incident_permission=lambda: True,
        replay=restored_hub,
    )
    for index in range(3):
        assert await restored.verify(
            notice("security_incident_reported", correlation_id=f"new-delivery-{index}")
        )
    assert [dict(event.facts) for event in restored_events] == [
        {"incident_state": "not_listed"},
        {"incident_state": "open"},
    ]
    assert restored_hub.get_resource_state("incident:123") == "open"
    assert "incident:123" not in str(restored_hub.export_replay())
    restored_hub.close()

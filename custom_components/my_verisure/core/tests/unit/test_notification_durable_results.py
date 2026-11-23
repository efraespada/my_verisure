"""Private semantic replay survives a changed transport delivery identifier.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.api import push_receiver
from custom_components.my_verisure.core.api.push_receiver import PushReceiver
from custom_components.my_verisure.core.file_manager import FileManager
from .test_notification_admission import envelope, make_hub
from .test_push_receiver import FakeClient


@pytest.mark.parametrize("invalid", ["", "x" * 1025, False, 7])
def test_invalid_private_result_key_is_rejected(invalid):
    with pytest.raises(ValueError, match="deduplication key"):
        make_hub().publish_verified("photo_ready", deduplication_key=invalid)


def test_signal_correlation_is_private_bounded_and_missing_is_unknown():
    hub = make_hub()
    for number in range(129):
        hub.receive(envelope(idSignal=str(number)), str(number))
    assert hub.correlation_for_signal(None) is None
    assert hub.correlation_for_signal("0") is None
    correlation = hub.correlation_for_signal("128")
    assert correlation and len(correlation) == 64
    event = hub.publish_verified(
        "photo_ready",
        correlation_id=correlation,
        deduplication_key="camera:private-signal",
        verification="image_commit",
    )
    assert event.correlation_id == correlation
    assert "private-signal" not in str(hub.diagnostics())


async def test_local_verified_replay_is_saved_without_waiting_for_another_push(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        push_receiver,
        "async_resolve_public_api_key",
        AsyncMock(return_value="synthetic-public-client-key"),
    )
    files, hub = FileManager(tmp_path), make_hub()
    receiver = PushReceiver(files, hub, client_factory=FakeClient)
    # No registered credentials means no file may be overwritten by a health tick.
    receiver.request_state_save()
    assert receiver._writer is None
    await receiver.async_prepare()
    hub.subscribe_diagnostics(receiver.request_state_save)
    hub.activate()
    first = hub.publish_verified(
        "photo_ready",
        deduplication_key="photo:private-immutable-signal",
        subject_entity_id="camera.synthetic",
        facts={"image_count": 3},
    )
    await receiver._writer
    stored = await receiver._store.load("push_credentials.json")
    restored = make_hub()
    restored.restore_replay(stored["notification_replay"])
    restored.activate()
    assert (
        restored.publish_verified(
            "photo_ready",
            correlation_id="different-delivery",
            deduplication_key="photo:private-immutable-signal",
        )
        is None
    )
    assert first is not None
    await receiver.async_stop()
    writer = receiver._writer
    receiver.request_state_save()
    assert receiver._writer is writer and (writer is None or writer.done())


@pytest.mark.parametrize(
    "key,state",
    [("", "open"), ("x" * 257, "open"), (False, "open"), ("incident", "closed")],
)
def test_resource_replay_rejects_unbounded_or_invented_states(key, state):
    with pytest.raises(ValueError, match="resource state"):
        make_hub().set_resource_state(key, state)


def test_resource_replay_is_private_bounded_and_expires():
    from .test_notification_admission import NOW

    stamp = [NOW]
    hub = make_hub(clock=lambda: stamp[0])
    for n in range(129):
        hub.set_resource_state(f"private-incident-{n}", "open")
    assert hub.get_resource_state("private-incident-0") is None
    assert hub.get_resource_state("private-incident-128") == "open"
    state = hub.export_replay()
    assert len(state["resources"]) == 128 and "private-incident" not in str(state)
    restored = make_hub(clock=lambda: stamp[0])
    restored.restore_replay(state)
    assert restored.get_resource_state("private-incident-128") == "open"
    stamp[0] += 86401
    assert restored.get_resource_state("private-incident-128") is None
    assert restored.export_replay()["resources"] == []
    hub.close()
    hub.set_resource_state("another", "open")
    assert hub.get_resource_state("another") is None


@pytest.mark.parametrize(
    "resources",
    [
        None,
        {},
        [None, [], ["a", "open", 1000]],
        [
            ["a" * 64, "closed", 1_800_000_000],
            ["b" * 64, "open", True],
            ["c" * 64, "open", float("nan")],
            ["d" * 64, "open", 1],
            ["e" * 64, "open", 1_800_000_061],
        ],
    ],
)
def test_invalid_resource_replay_does_not_create_state(resources):
    hub = make_hub()
    hub.restore_replay({"version": 1, "seen": [], "resources": resources})
    assert hub.export_replay()["resources"] == []


def test_restoring_twice_keeps_one_bounded_resource_ledger():
    from .test_notification_admission import NOW

    hub = make_hub()
    for offset in (0, 128):
        hub.restore_replay(
            {
                "version": 1,
                "seen": [],
                "resources": [
                    [f"{n:064x}", "open", NOW] for n in range(offset, offset + 128)
                ],
            }
        )
    assert len(hub.export_replay()["resources"]) == 128

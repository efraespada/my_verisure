"""Do not turn late startup transport backlog into live household activity.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import json

import pytest

from custom_components.my_verisure.core.api.notification_mapper import (
    NotificationMapper,
)
from custom_components.my_verisure.core.application.notifications import NotificationHub


@pytest.mark.parametrize("activate_before_connect", [False, True])
def test_first_connection_after_restart_reconciles_undelivered_backlog(
    activate_before_connect,
):
    """The replay ledger cannot recognize messages never delivered before restart."""
    now = [1000.0]
    old = NotificationHub(
        "synthetic-entry",
        NotificationMapper("synthetic-home", "synthetic-entry"),
        clock=lambda: now[0],
    )
    restored = NotificationHub(
        "synthetic-entry",
        NotificationMapper("synthetic-home", "synthetic-entry"),
        clock=lambda: now[0],
    )
    restored.restore_ids(old.recent_ids)
    restored.restore_replay(old.export_replay())
    events, hints = [], []
    restored.subscribe(events.append)
    restored.subscribe_hints(hints.append)
    if activate_before_connect:
        restored.activate()
    restored.connected = True
    if not activate_before_connect:
        restored.activate()
    hints.clear()  # A private baseline reconciliation is allowed at connection.
    restored.receive(
        {
            "data": {
                "text": json.dumps(
                    {
                        "request": "ARMDISARM",
                        "numinst": "synthetic-home",
                        "timeStamp": 990_000,
                    }
                )
            }
        },
        "synthetic-undelivered-backlog",
    )
    assert not events
    assert not hints
    assert restored.diagnostics()["recent"][-1]["delivery"] == "reconciled"
    now[0] = 1001.0
    restored.receive(
        {
            "data": {
                "text": json.dumps(
                    {
                        "request": "ARMDISARM",
                        "numinst": "synthetic-home",
                        "timeStamp": 1_001_000,
                    }
                )
            }
        },
        "synthetic-new-live-delivery",
    )
    assert len(events) == len(hints) == 1
    assert events[0].delivery == "live"

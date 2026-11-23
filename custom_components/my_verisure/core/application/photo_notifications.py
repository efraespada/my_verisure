"""Bounded photo hints; notifications never initiate provider operations.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from collections import deque
import json
import time
from typing import Any


class PhotoNotifications:
    """One pending camera request and a bounded replay history per entry."""

    def __init__(self) -> None:
        self.connected = False
        self._closed = False
        self._pending: tuple[str, float] | None = None
        self._signals: deque[str] = deque(maxlen=2)
        self._recent: deque[str] = deque(maxlen=128)
        self._ready = asyncio.Event()

    @property
    def pending(self) -> bool:
        """Tell independent consumers that the local capture owns this delivery."""
        return self._pending is not None and not self._closed

    @property
    def recent_ids(self) -> list[str]:
        return list(self._recent)

    def restore_ids(self, values: list[str]) -> None:
        self._recent.extend(value for value in values[-128:] if isinstance(value, str))

    def begin(self, installation_id: str, started_at: float) -> None:
        if self._closed:
            raise asyncio.CancelledError
        if self._pending is not None:
            raise RuntimeError("A photo request is already pending")
        self._pending = (installation_id, started_at)
        self._signals.clear()
        self._ready.clear()

    def finish(self) -> None:
        self._pending = None
        self._signals.clear()

    def close(self) -> None:
        self._closed = True
        self.connected = False
        self._ready.set()

    def receive(self, payload: dict[str, Any], persistent_id: str) -> None:
        if not isinstance(persistent_id, str) or not 0 < len(persistent_id) <= 512:
            return
        if persistent_id in self._recent:
            return
        self._recent.append(persistent_id)
        if self._pending is None or self._closed:
            return
        try:
            text = payload["data"]["text"]
            if not isinstance(text, str) or len(text) > 8192:
                return
            event = json.loads(text)
            installation, started = self._pending
            if event.get("request") != "INF" or event.get("type") != 0:
                return
            if str(event.get("numinst")) != installation:
                return
            timestamp = int(event["timeStamp"]) / 1000
            if timestamp < started - 2 or timestamp > time.time() + 60:
                return
            signal = str(event["idSignal"])
            if not signal.isdigit() or len(signal) > 128:
                return
            self._signals.append(signal)
            self._ready.set()
        except (KeyError, TypeError, ValueError, AttributeError):
            return

    async def wait(self, timeout: float) -> str | None:
        if not self._signals:
            try:
                await asyncio.wait_for(self._ready.wait(), timeout)
            except TimeoutError:
                return None
        if self._closed:
            raise asyncio.CancelledError
        signal = self._signals.popleft() if self._signals else None
        if not self._signals:
            self._ready.clear()
        return signal

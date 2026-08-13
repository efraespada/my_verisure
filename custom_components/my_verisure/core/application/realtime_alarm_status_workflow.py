"""Application workflow for polling realtime alarm status."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from .realtime_alarm_status import (
    RealtimeAlarmStatusInterpreter,
    RealtimeStatusAction,
)

RealtimeTransport = Callable[[int], Awaitable[Mapping[str, Any]]]


class RealtimeAlarmStatusWorkflow:
    """Poll and normalize the provider's realtime alarm status response."""

    def __init__(
        self,
        interpreter: RealtimeAlarmStatusInterpreter | None = None,
        *,
        max_retries: int = 10,
        retry_delay_seconds: float = 15,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be positive")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")
        self._interpreter = interpreter or RealtimeAlarmStatusInterpreter()
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._sleep = sleep

    async def run(self, transport: RealtimeTransport) -> str:
        """Poll until a terminal response, exhaustion, or transport failure."""
        for attempt in range(self._max_retries):
            try:
                result = await transport(attempt)
            except Exception:
                return ""

            decision = self._interpreter.interpret(result)
            if decision.action is RealtimeStatusAction.SUCCESS:
                return decision.message
            if decision.action is RealtimeStatusAction.FAILURE:
                return decision.message
            if decision.action is RealtimeStatusAction.EMPTY:
                return ""

            if attempt + 1 < self._max_retries:
                await self._sleep(self._retry_delay_seconds)

        return ""

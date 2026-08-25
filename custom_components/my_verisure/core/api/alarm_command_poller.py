"""Application service for polling alarm command completion.

The poller knows the Verisure response contract but has no HTTP, Home
Assistant, session, or filesystem dependency. The API adapter supplies the
status transport callback.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from ..application.models.alarm import ArmResult, DisarmResult

StatusTransport = Callable[[int], Awaitable[Mapping[str, Any]]]


class AlarmCommandPoller:
    """Poll arm and disarm command status responses."""

    def __init__(self, *, max_retries: int = 30, retry_delay: float = 15.0) -> None:
        if max_retries < 1:
            raise ValueError("max_retries must be positive")
        if retry_delay < 0:
            raise ValueError("retry_delay cannot be negative")
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def poll_arm(
        self,
        transport: StatusTransport,
        *,
        reference_id: str,
    ) -> ArmResult:
        """Poll arm status until completion or exhaustion."""
        for attempt in range(1, self._max_retries + 1):
            result = await transport(attempt)
            if self._has_graphql_error(result):
                return ArmResult(
                    success=False,
                    message="Alarm service request failed",
                    reference_id=reference_id,
                )

            payload = self._payload(result, "xSArmStatus")
            response_code = self._response_code(payload)
            if response_code == "OK":
                return ArmResult(True, "Alarm command accepted", reference_id)
            if response_code != "WAIT":
                return ArmResult(False, "Alarm command rejected", reference_id)
            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_delay)

        return ArmResult(False, "Alarm command polling exhausted", reference_id)

    async def poll_disarm(
        self,
        transport: StatusTransport,
        *,
        reference_id: str,
    ) -> DisarmResult:
        """Poll disarm status until completion or exhaustion."""
        for attempt in range(1, self._max_retries + 1):
            result = await transport(attempt)
            if self._has_graphql_error(result):
                return DisarmResult(
                    success=False,
                    message="Alarm service request failed",
                    reference_id=reference_id,
                )

            payload = self._payload(result, "xSDisarmStatus")
            response_code = self._response_code(payload)
            if response_code == "OK":
                return DisarmResult(True, "Disarm command accepted", reference_id)
            if response_code != "WAIT":
                return DisarmResult(False, "Disarm command rejected", reference_id)
            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_delay)

        return DisarmResult(False, "Disarm command polling exhausted", reference_id)

    @staticmethod
    def _has_graphql_error(result: Mapping[str, Any]) -> bool:
        """Return whether the response contains a non-empty or malformed errors field."""
        if "errors" not in result:
            return False
        return "errors" in result

    @staticmethod
    def _payload(result: Mapping[str, Any], key: str) -> Mapping[str, Any]:
        data = result.get("data")
        if not isinstance(data, Mapping):
            return {}
        payload = data.get(key)
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _response_code(payload: Mapping[str, Any]) -> str:
        """Read only the bounded response code used by the state machine."""
        value = payload.get("res")
        return value if isinstance(value, str) else "UNKNOWN"

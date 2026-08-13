"""Application service for polling alarm command completion.

The poller knows the Verisure response contract but has no HTTP, Home
Assistant, session, or filesystem dependency. The API adapter supplies the
status transport callback.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from ..api.models.domain.alarm import ArmResult, DisarmResult

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
            error = self._graphql_error(result)
            if error is not None:
                return ArmResult(success=False, message=error, reference_id=reference_id)

            payload = self._payload(result, "xSArmStatus")
            response = self._response_fields(payload)
            response_code = response["res"]
            message = response["msg"]
            if response_code == "OK":
                return ArmResult(True, message, reference_id)
            if response_code != "WAIT":
                return ArmResult(False, message, reference_id)
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
            error = self._graphql_error(result)
            if error is not None:
                return DisarmResult(success=False, message=error, reference_id=reference_id)

            payload = self._payload(result, "xSDisarmStatus")
            response = self._response_fields(payload)
            response_code = response["res"]
            message = response["msg"]
            if response_code == "OK":
                return DisarmResult(True, message, reference_id)
            if response_code != "WAIT":
                return DisarmResult(False, message, reference_id)
            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_delay)

        return DisarmResult(False, "Disarm command polling exhausted", reference_id)

    @staticmethod
    def _graphql_error(result: Mapping[str, Any]) -> str | None:
        errors = result.get("errors")
        if not errors:
            return None
        first_error = errors[0] if isinstance(errors, list) else {}
        if isinstance(first_error, Mapping):
            return str(first_error.get("message", "Unknown error"))
        return "Unknown error"

    @staticmethod
    def _payload(result: Mapping[str, Any], key: str) -> Mapping[str, Any]:
        data = result.get("data")
        if not isinstance(data, Mapping):
            return {}
        payload = data.get(key)
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _response_fields(payload: Mapping[str, Any]) -> dict[str, str]:
        return {
            "res": str(payload.get("res", "Unknown")),
            "msg": str(payload.get("msg", "Unknown")),
        }

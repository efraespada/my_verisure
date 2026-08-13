"""Interpretation of Verisure realtime alarm status responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class RealtimeStatusAction(StrEnum):
    """Action requested by a realtime status response."""

    SUCCESS = "success"
    FAILURE = "failure"
    WAIT = "wait"
    EMPTY = "empty"


@dataclass(frozen=True)
class RealtimeStatusDecision:
    """Normalized realtime status response."""

    action: RealtimeStatusAction
    message: str = ""


class RealtimeAlarmStatusInterpreter:
    """Translate raw GraphQL realtime status responses into application decisions."""

    def interpret(self, result: Mapping[str, Any]) -> RealtimeStatusDecision:
        """Interpret one response without performing I/O or logging."""
        error = self._graphql_error(result)
        if error is not None:
            return RealtimeStatusDecision(RealtimeStatusAction.EMPTY)

        payload = self._payload(result)
        response = self._response_fields(payload)
        code = response["res"]
        message = response["msg"]

        if code == "OK":
            return RealtimeStatusDecision(RealtimeStatusAction.SUCCESS, message)
        if code == "KO":
            return RealtimeStatusDecision(RealtimeStatusAction.FAILURE, message)
        if code == "WAIT":
            return RealtimeStatusDecision(RealtimeStatusAction.WAIT, message)
        return RealtimeStatusDecision(RealtimeStatusAction.EMPTY)

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
    def _payload(result: Mapping[str, Any]) -> Mapping[str, Any]:
        data = result.get("data")
        if not isinstance(data, Mapping):
            return {}
        payload = data.get("xSCheckAlarmStatus")
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _response_fields(payload: Mapping[str, Any]) -> dict[str, str]:
        return {
            "res": str(payload.get("res", "Unknown")),
            "msg": str(payload.get("msg", "Unknown")),
        }

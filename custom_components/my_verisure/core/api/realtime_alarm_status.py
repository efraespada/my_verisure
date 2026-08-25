"""Interpretation of Verisure realtime alarm status responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..application.exceptions import MyVerisureError


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
        if not isinstance(result, Mapping):
            raise MyVerisureError("Invalid realtime alarm status response") from None
        if "errors" in result:
            raise MyVerisureError("Invalid realtime alarm status response") from None

        payload = self._payload(result)
        if not payload:
            raise MyVerisureError("Invalid realtime alarm status response") from None
        response = self._response_fields(payload)
        code = response["res"]

        message = response["msg"]
        if code == "OK":
            return RealtimeStatusDecision(RealtimeStatusAction.SUCCESS, message)
        if code == "KO":
            return RealtimeStatusDecision(RealtimeStatusAction.FAILURE, message)
        if code == "WAIT":
            return RealtimeStatusDecision(RealtimeStatusAction.WAIT, message)
        raise MyVerisureError("Invalid realtime alarm status response") from None

    @staticmethod
    def _has_graphql_error(result: Mapping[str, Any]) -> bool:
        """Return whether GraphQL errors are non-empty or malformed."""
        if "errors" not in result:
            return False
        return "errors" in result

    @staticmethod
    def _payload(result: Mapping[str, Any]) -> Mapping[str, Any]:
        data = result.get("data")
        if not isinstance(data, Mapping):
            return {}
        payload = data.get("xSCheckAlarmStatus")
        return payload if isinstance(payload, Mapping) else {}

    @staticmethod
    def _response_fields(payload: Mapping[str, Any]) -> dict[str, str]:
        code = payload.get("res")
        if not isinstance(code, str) or not code.strip():
            raise MyVerisureError("Invalid realtime alarm status response") from None
        message = payload.get("msg")
        if not isinstance(message, str) or not message.strip():
            raise MyVerisureError("Invalid realtime alarm status response") from None
        return {"res": code, "msg": message}

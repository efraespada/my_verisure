"""Interpret initial alarm command GraphQL responses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AlarmCommandResponse:
    """Normalized response returned by an arm/disarm mutation."""

    accepted: bool
    message: str
    reference_id: str | None = None


class AlarmCommandResponseInterpreter:
    """Translate mutation payloads without transport or domain dependencies."""

    def interpret(
        self,
        result: Mapping[str, Any],
        *,
        payload_key: str,
    ) -> AlarmCommandResponse:
        """Interpret one initial command response."""
        graphql_message = self._graphql_error(result)
        if graphql_message is not None:
            return AlarmCommandResponse(False, graphql_message)

        payload = self._payload(result, payload_key)
        response_code = str(payload.get("res", "Unknown"))
        message = str(payload.get("msg", "Unknown"))
        reference_id = payload.get("referenceId")

        if response_code != "OK":
            return AlarmCommandResponse(False, message)
        if not reference_id:
            return AlarmCommandResponse(False, "Missing command reference")
        return AlarmCommandResponse(True, message, str(reference_id))

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
    def _payload(
        result: Mapping[str, Any], payload_key: str
    ) -> Mapping[str, Any]:
        data = result.get("data")
        if not isinstance(data, Mapping):
            return {}
        payload = data.get(payload_key)
        return payload if isinstance(payload, Mapping) else {}

"""Application workflow for arm and disarm command execution."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from ..api.models.domain.alarm import ArmResult, DisarmResult
from .alarm_command_poller import AlarmCommandPoller, StatusTransport
from .alarm_command_response import AlarmCommandResponseInterpreter

CommandTransport = Callable[[], Awaitable[Mapping[str, Any]]]
StatusTransportFactory = Callable[[str], StatusTransport]


class AlarmCommandWorkflow:
    """Coordinate initial command acceptance and completion polling."""

    def __init__(
        self,
        *,
        interpreter: AlarmCommandResponseInterpreter | None = None,
        poller: AlarmCommandPoller | None = None,
    ) -> None:
        self._interpreter = interpreter or AlarmCommandResponseInterpreter()
        self._poller = poller or AlarmCommandPoller()

    async def arm(
        self,
        command_transport: CommandTransport,
        status_transport_factory: StatusTransportFactory,
    ) -> ArmResult:
        """Execute and poll an arm command."""
        response = self._interpreter.interpret(
            await command_transport(),
            payload_key="xSArmPanel",
        )
        if not response.accepted:
            return ArmResult(success=False, message=response.message)
        if response.reference_id is None:
            return ArmResult(success=False, message="Missing command reference")
        return await self._poller.poll_arm(
            status_transport_factory(response.reference_id),
            reference_id=response.reference_id,
        )

    async def disarm(
        self,
        command_transport: CommandTransport,
        status_transport_factory: StatusTransportFactory,
    ) -> DisarmResult:
        """Execute and poll a disarm command."""
        response = self._interpreter.interpret(
            await command_transport(),
            payload_key="xSDisarmPanel",
        )
        if not response.accepted:
            return DisarmResult(success=False, message=response.message)
        if response.reference_id is None:
            return DisarmResult(success=False, message="Missing command reference")
        return await self._poller.poll_disarm(
            status_transport_factory(response.reference_id),
            reference_id=response.reference_id,
        )

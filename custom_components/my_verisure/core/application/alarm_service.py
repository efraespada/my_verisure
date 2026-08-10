"""Application service for dispatching alarm commands by installation."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol, TypeAlias

from ..api.models.domain.alarm import ArmResult, DisarmResult


AlarmCommandResult: TypeAlias = ArmResult | DisarmResult


class AlarmCoordinator(Protocol):
    """Minimum coordinator contract required by the application service."""

    config_entry: object

    async def async_arm_away(self) -> ArmResult:
        """Arm the installation away."""
        ...

    async def async_arm_home(self) -> ArmResult:
        """Arm the installation home."""
        ...

    async def async_arm_night(self) -> ArmResult:
        """Arm the installation at night."""
        ...

    async def async_disarm(self) -> DisarmResult:
        """Disarm the installation."""
        ...


CoordinatorOperation: TypeAlias = Callable[
    [AlarmCoordinator], Awaitable[AlarmCommandResult]
]


@dataclass(frozen=True)
class AlarmServiceDispatcher:
    """Dispatch allowlisted alarm commands without HA-specific concerns."""

    coordinators: Iterable[AlarmCoordinator]

    async def dispatch(
        self,
        installation_id: str,
        command: str,
    ) -> AlarmCommandResult:
        """Dispatch one command to the coordinator for an installation."""
        operation = self._operation(command)
        if operation is None:
            return ArmResult(success=False, message=f"Command {command} not supported")

        for coordinator in self.coordinators:
            data = getattr(coordinator.config_entry, "data", {})
            if not isinstance(data, Mapping):
                continue
            if data.get("installation_id") != installation_id:
                continue
            try:
                return await operation(coordinator)
            except Exception as error:
                return ArmResult(success=False, message=str(error))

        return ArmResult(
            success=False,
            message=f"Installation {installation_id} not found",
        )

    @staticmethod
    def _operation(command: str) -> CoordinatorOperation | None:
        operations: dict[str, CoordinatorOperation] = {
            "async_arm_away": lambda coordinator: coordinator.async_arm_away(),
            "async_arm_home": lambda coordinator: coordinator.async_arm_home(),
            "async_arm_night": lambda coordinator: coordinator.async_arm_night(),
            "async_disarm": lambda coordinator: coordinator.async_disarm(),
        }
        return operations.get(command)

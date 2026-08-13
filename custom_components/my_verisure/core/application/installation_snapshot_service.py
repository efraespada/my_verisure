"""Application service for refreshing installation and alarm snapshots."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Protocol

from ..api.models.dto.installation_dto import DetailedInstallationDTO
from .coordinator_snapshot import build_coordinator_snapshot


class InstallationSnapshotReader(Protocol):
    """Port for reading the detailed installation."""

    async def get_installation_services(self, installation_id: str) -> DetailedInstallationDTO:
        """Return the detailed installation."""
        ...


class AlarmSnapshotReader(Protocol):
    """Port for reading the alarm state."""

    async def get_alarm_status(
        self,
        installation_id: str,
        *,
        panel: str,
        capabilities: str,
    ) -> Any:
        """Return the current alarm status."""


class InstallationSnapshotService:
    """Coordinate application reads and build the canonical snapshot."""

    def __init__(
        self,
        installation_reader: InstallationSnapshotReader,
        alarm_reader: AlarmSnapshotReader,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._installation_reader = installation_reader
        self._alarm_reader = alarm_reader
        self._clock = clock

    async def refresh(self, installation_id: str) -> dict[str, Any]:
        """Read installation and alarm data and assemble a persisted snapshot."""
        detailed_installation = await self._installation_reader.get_installation_services(
            installation_id
        )
        panel = detailed_installation.installation.panel or "PROTOCOL"
        capabilities = (
            detailed_installation.installation.capabilities or "default_capabilities"
        )
        alarm_status = await self._alarm_reader.get_alarm_status(
            installation_id,
            panel=panel,
            capabilities=capabilities,
        )
        return build_coordinator_snapshot(
            installation_id=installation_id,
            alarm_status=alarm_status.dict(),
            detailed_installation=detailed_installation.to_dict(),
            timestamp=self._clock(),
        )

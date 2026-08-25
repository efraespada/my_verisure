"""Tests for the installation snapshot application service."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.installation_snapshot_service import (
    InstallationSnapshotService,
)


@pytest.mark.asyncio
async def test_refresh_reads_installation_and_alarm_and_builds_snapshot() -> None:
    installation = Mock()
    installation.installation.panel = "PANEL"
    installation.installation.capabilities = "CAPS"
    installation.dict.return_value = {"installation": {"panel": "PANEL"}}

    alarm = Mock()
    alarm.dict.return_value = {"status": "armed"}

    installation_reader = Mock()
    installation_reader.get_installation_services = AsyncMock(return_value=installation)
    alarm_reader = Mock()
    alarm_reader.get_alarm_status = AsyncMock(return_value=alarm)

    service = InstallationSnapshotService(
        installation_reader,
        alarm_reader,
        clock=lambda: 123.0,
    )
    result = await service.refresh("home-1")

    assert result == {
        "last_updated": 123.0,
        "installation_id": "home-1",
        "alarm_status": {"status": "armed"},
        "detailed_installation": {"installation": {"panel": "PANEL"}},
    }
    alarm_reader.get_alarm_status.assert_awaited_once_with(
        "home-1", panel="PANEL", capabilities="CAPS"
    )


@pytest.mark.asyncio
async def test_refresh_rejects_missing_capabilities() -> None:
    installation = Mock()
    installation.installation.panel = None
    installation.installation.capabilities = None
    installation.dict.return_value = {}

    installation_reader = Mock()
    installation_reader.get_installation_services = AsyncMock(return_value=installation)
    alarm_reader = Mock()

    with pytest.raises(MyVerisureError, match="Installation context unavailable"):
        await InstallationSnapshotService(installation_reader, alarm_reader).refresh("home-2")

    alarm_reader.get_alarm_status.assert_not_called()

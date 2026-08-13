"""Unit tests for current alarm repository contracts."""

from unittest.mock import AsyncMock, Mock

import pytest

from ....api.exceptions import MyVerisureError
from ....api.models.domain.alarm import ArmResult, DisarmResult
from ....repositories.implementations.alarm_repository_impl import AlarmRepositoryImpl
from ....repositories.interfaces.alarm_repository import AlarmRepository


@pytest.fixture
def client():
    value = Mock()
    value.get_alarm_status = AsyncMock()
    value.arm_alarm_away = AsyncMock()
    value.arm_alarm_home = AsyncMock()
    value.arm_alarm_night = AsyncMock()
    value.disarm_alarm = AsyncMock()
    return value


@pytest.fixture
def repository(client):
    return AlarmRepositoryImpl(client)


def test_implements_interface(repository):
    assert isinstance(repository, AlarmRepository)


@pytest.mark.asyncio
async def test_status_maps_processed_response(repository, client):
    client.get_alarm_status.return_value = {
        "internal": {"day": {"status": True}}, "external": {}
    }
    result = await repository.get_alarm_status("1", "panel", "caps")
    assert result.success is True
    assert result.status == "ALARM"
    assert result.message == "Internal day alarm active"
    client.get_alarm_status.assert_awaited_once_with("1", "panel", "caps")


@pytest.mark.asyncio
async def test_status_error_propagates(repository, client):
    client.get_alarm_status.side_effect = MyVerisureError("connection")
    with pytest.raises(MyVerisureError, match="connection"):
        await repository.get_alarm_status("1", "panel", "caps")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "client_method"),
    [("arm_away", "arm_alarm_away"), ("arm_home", "arm_alarm_home"), ("arm_night", "arm_alarm_night")],
)
async def test_arm_modes_delegate(repository, client, method, client_method):
    expected = ArmResult(True, "armed")
    getattr(client, client_method).return_value = expected
    result = await getattr(repository, method)("1", "panel", "caps")
    assert result == expected
    getattr(client, client_method).assert_awaited_once_with("1", "panel", "caps")


@pytest.mark.asyncio
async def test_arm_panel_preserves_failed_result(repository, client):
    expected = ArmResult(False, "provider rejected")
    client.arm_alarm_away.return_value = expected

    result = await repository.arm_panel("1", "ARM1", "panel", "caps")

    assert result == expected


@pytest.mark.asyncio
async def test_arm_away_can_arm_perimeter(repository, client):
    client.arm_alarm_away.return_value = ArmResult(True, "away")
    client.arm_alarm_home.return_value = ArmResult(True, "home")
    result = await repository.arm_away("1", "panel", "caps", True)
    assert result.message == "home"
    client.arm_alarm_home.assert_awaited_once_with("1", "panel", "caps")


@pytest.mark.asyncio
async def test_disarm_delegates(repository, client):
    expected = DisarmResult(True, "disarmed")
    client.disarm_alarm.return_value = expected
    result = await repository.disarm_panel("1", "panel", "caps")
    assert result == expected
    client.disarm_alarm.assert_awaited_once_with("1", "panel", capabilities="caps")

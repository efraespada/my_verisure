"""Tests for the application-level alarm service dispatcher."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.application.alarm_service import (
    AlarmServiceDispatcher,
)


@pytest.fixture
def coordinator():
    value = SimpleNamespace(
        config_entry=SimpleNamespace(data={"installation_id": "home-1"}),
        async_arm_away=AsyncMock(
            return_value=SimpleNamespace(success=True, message="ok")
        ),
    )
    return value


@pytest.mark.asyncio
async def test_dispatches_command_to_matching_installation(coordinator):
    dispatcher = AlarmServiceDispatcher([coordinator])

    result = await dispatcher.dispatch("home-1", "async_arm_away")

    assert result.success is True
    coordinator.async_arm_away.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_returns_failure_for_unknown_installation(coordinator):
    dispatcher = AlarmServiceDispatcher([coordinator])

    result = await dispatcher.dispatch("missing", "async_arm_away")

    assert result.success is False
    assert result.message == "Installation missing not found"


@pytest.mark.asyncio
async def test_rejects_non_allowlisted_command(coordinator):
    dispatcher = AlarmServiceDispatcher([coordinator])

    result = await dispatcher.dispatch("home-1", "delete_configuration")

    assert result.success is False
    assert result.message == "Command delete_configuration not supported"


@pytest.mark.asyncio
async def test_returns_failure_when_command_raises(coordinator):
    coordinator.async_arm_away.side_effect = RuntimeError("network down")
    dispatcher = AlarmServiceDispatcher([coordinator])

    result = await dispatcher.dispatch("home-1", "async_arm_away")

    assert result.success is False
    assert result.message == "network down"

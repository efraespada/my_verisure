"""Focused tests for Home Assistant service dispatch boundaries."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.my_verisure import services


def _coordinator(installation_id: str, *, result=None, error=None):
    command = AsyncMock(return_value=result, side_effect=error)
    return SimpleNamespace(
        config_entry=SimpleNamespace(data={"installation_id": installation_id}),
        async_arm_away=command,
        clear_alarm_transition_state=Mock(),
    )


@pytest.mark.asyncio
async def test_dispatch_alarm_service_updates_matching_coordinator() -> None:
    coordinator = _coordinator(
        "home-1", result=SimpleNamespace(success=True, message="ok")
    )
    hass = SimpleNamespace()

    with patch.object(services, "_iter_coordinators", return_value=(coordinator,)):
        await services._dispatch_alarm_service(
            hass, "home-1", "async_arm_away", "arm away"
        )

    coordinator.async_arm_away.assert_awaited_once_with()
    coordinator.clear_alarm_transition_state.assert_called_once_with()


@pytest.mark.asyncio
async def test_dispatch_alarm_service_reports_failed_command() -> None:
    coordinator = _coordinator(
        "home-1", result=SimpleNamespace(success=False, message="rejected")
    )
    hass = SimpleNamespace()

    with patch.object(services, "_iter_coordinators", return_value=(coordinator,)):
        await services._dispatch_alarm_service(
            hass, "home-1", "async_arm_away", "arm away"
        )

    coordinator.async_arm_away.assert_awaited_once_with()
    coordinator.clear_alarm_transition_state.assert_called_once_with()


@pytest.mark.asyncio
async def test_dispatch_alarm_service_handles_unknown_installation() -> None:
    coordinator = _coordinator(
        "home-1", result=SimpleNamespace(success=True, message="ok")
    )
    hass = SimpleNamespace()

    with patch.object(services, "_iter_coordinators", return_value=(coordinator,)):
        await services._dispatch_alarm_service(
            hass, "missing", "async_arm_away", "arm away"
        )

    coordinator.async_arm_away.assert_not_awaited()
    coordinator.clear_alarm_transition_state.assert_not_called()

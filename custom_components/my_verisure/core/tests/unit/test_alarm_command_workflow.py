"""Tests for the arm/disarm command workflow."""

from unittest.mock import AsyncMock

import pytest

from custom_components.my_verisure.core.application.alarm_command_workflow import (
    AlarmCommandWorkflow,
)
from custom_components.my_verisure.core.application.alarm_command_poller import (
    AlarmCommandPoller,
)


@pytest.mark.asyncio
async def test_arm_workflow_accepts_reference_and_polls():
    command = AsyncMock(
        return_value={
            "data": {"xSArmPanel": {"res": "OK", "msg": "accepted", "referenceId": "r1"}}
        }
    )
    status = AsyncMock(
        return_value={"data": {"xSArmStatus": {"res": "OK", "msg": "armed"}}}
    )

    result = await AlarmCommandWorkflow(
        poller=AlarmCommandPoller(max_retries=1, retry_delay=0)
    ).arm(command, lambda _: status)

    assert result.success is True
    assert result.message == "armed"
    command.assert_awaited_once()
    status.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_disarm_workflow_rejects_initial_response():
    command = AsyncMock(
        return_value={"data": {"xSDisarmPanel": {"res": "KO", "msg": "rejected"}}}
    )
    status = AsyncMock()

    result = await AlarmCommandWorkflow().disarm(command, status)

    assert result.success is False
    assert result.message == "rejected"
    status.assert_not_awaited()


@pytest.mark.asyncio
async def test_arm_workflow_reports_missing_reference():
    command = AsyncMock(
        return_value={"data": {"xSArmPanel": {"res": "OK", "msg": "accepted"}}}
    )

    result = await AlarmCommandWorkflow().arm(
        command,
        lambda _: AsyncMock(),
    )

    assert result.success is False
    assert result.message == "Missing command reference"

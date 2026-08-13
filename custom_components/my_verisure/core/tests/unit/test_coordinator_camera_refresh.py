"""Tests for coordinator camera refresh orchestration."""

from unittest.mock import AsyncMock, Mock
from datetime import datetime

import pytest

from custom_components.my_verisure.core.api.models.domain.camera_refresh import CameraRefresh
from custom_components.my_verisure.core.application.coordinator_camera_refresh import (
    CameraRefreshPolicy,
    CoordinatorCameraRefresh,
)


@pytest.mark.asyncio
async def test_run_uses_stable_polling_policy_and_returns_result() -> None:
    executor = Mock()
    result = CameraRefresh([], 2, 1, 1, datetime.now().isoformat())
    executor.refresh_camera_images = AsyncMock(return_value=result)
    refresh = CoordinatorCameraRefresh(
        executor,
        CameraRefreshPolicy(max_attempts=5, check_interval=2),
    )

    actual = await refresh.run("home-1")

    assert actual is result
    executor.refresh_camera_images.assert_awaited_once_with(
        installation_id="home-1",
        max_attempts=5,
        check_interval=2,
    )


@pytest.mark.asyncio
async def test_run_propagates_executor_failure() -> None:
    executor = Mock()
    executor.refresh_camera_images = AsyncMock(side_effect=RuntimeError("offline"))
    refresh = CoordinatorCameraRefresh(executor)

    with pytest.raises(RuntimeError, match="offline"):
        await refresh.run("home-1")

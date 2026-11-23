"""Expose committed local captures without publishing partial or failed photos.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.models.device import Device
from custom_components.my_verisure.core.application.notification_verification import (
    NotificationVerifier,
    VerifiedPhoto,
)
from ...use_cases.implementations.refresh_camera_images_use_case_impl import (
    RefreshCameraImagesUseCaseImpl,
)


def capture(*, success=True, push_signal="123"):
    camera = SimpleNamespace(
        request_image=AsyncMock(
            return_value=SimpleNamespace(successful_requests=1, signal_id=push_signal)
        ),
        get_images=AsyncMock(
            return_value={
                "success": success,
                "images_saved": 3 if success else 1,
                "signal_id": "123",
            }
        ),
    )
    installation = SimpleNamespace(
        get_installation_services=AsyncMock(
            return_value=SimpleNamespace(
                installation=SimpleNamespace(
                    panel="synthetic-panel",
                    capabilities="synthetic-caps",
                    devices=[
                        Device(
                            "synthetic-device",
                            "7",
                            "synthetic",
                            "YR",
                            "",
                            True,
                            "CAM",
                            True,
                        )
                    ],
                )
            )
        )
    )
    return RefreshCameraImagesUseCaseImpl(camera, installation), camera


@pytest.mark.parametrize("push_signal", ["123", None])
async def test_successful_photo_callback_after_commit_keeps_push_and_polling_contract(
    monkeypatch, push_signal
):
    value, camera = capture(push_signal=push_signal)
    callback = Mock()
    value.set_photo_committed_callback(callback)
    sleep = AsyncMock()
    monkeypatch.setattr(asyncio, "sleep", sleep)
    result = await value.refresh_camera_images(
        "synthetic-house", max_attempts=3, check_interval=20
    )
    assert result.successful_refreshes == 1
    callback.assert_called_once_with("YR07", 3, "123")
    camera.request_image.assert_awaited_once()
    assert camera.request_image.await_args.kwargs["max_attempts"] == 3
    assert camera.request_image.await_args.kwargs["check_interval"] == 20
    assert sleep.await_count == int(push_signal is None)


async def test_partial_image_failure_emits_no_photo_ready():
    value, camera = capture(success=False)
    callback = Mock()
    value.set_photo_committed_callback(callback)
    result = await value.refresh_camera_images("synthetic-house")
    assert result.failed_refreshes == 1
    callback.assert_not_called()


async def test_observer_failure_does_not_turn_committed_capture_into_failure():
    value, camera = capture()
    value.set_photo_committed_callback(
        Mock(side_effect=RuntimeError("synthetic observer failure"))
    )
    result = await value.refresh_camera_images("synthetic-house")
    assert result.successful_refreshes == 1


async def test_cancelled_image_retrieval_never_publishes_completion():
    value, camera = capture()
    camera.get_images.side_effect = asyncio.CancelledError
    callback = Mock()
    value.set_photo_committed_callback(callback)
    with pytest.raises(asyncio.CancelledError):
        await value.refresh_camera_images("synthetic-house")
    callback.assert_not_called()


async def test_local_and_external_paths_share_photo_deduplication():
    hub = Mock()
    consumer = NotificationVerifier(hub)
    photo = VerifiedPhoto("camera.synthetic", 3)
    assert consumer.publish_photo(photo, signal_id="123", origin="local_request")
    assert not consumer.publish_photo(photo, signal_id="123", origin="provider_notice")
    hub.publish_verified.assert_called_once()

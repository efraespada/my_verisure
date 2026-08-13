"""Characterization tests for CameraClient request and retrieval branches."""

from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.api.exceptions import MyVerisureError
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.fixture
def camera_client(tmp_path) -> CameraClient:
    file_manager = FileManager(tmp_path)
    session_manager = SessionManager(file_manager=file_manager)
    session_manager.hash_token = "session-hash"
    session_manager.username = "user"
    session_manager.password = "password"
    setattr(
        session_manager,
        "get_current_session_data",
        Mock(return_value={"user": "user", "lang": "ES"}),
    )
    result = CameraClient(
        session_manager=session_manager,
        file_manager=file_manager,
    )
    return result


def _set_query_results(client: CameraClient, results: list[dict[str, Any]]) -> AsyncMock:
    query = AsyncMock(side_effect=results)
    setattr(client, "_execute_query_direct", query)
    return query


@pytest.mark.asyncio
async def test_request_image_completes_after_processing_status(
    camera_client: CameraClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    query = _set_query_results(
        camera_client,
        [
            {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref-1"}}},
            {
                "data": {
                    "xSRequestImagesStatus": {
                        "res": "OK",
                        "msg": "alarm-manager.photo-request.processing",
                    }
                }
            },
            {
                "data": {
                    "xSRequestImagesStatus": {
                        "res": "OK",
                        "msg": "completed",
                    }
                }
            },
        ],
    )

    result = await camera_client.request_image("installation", "panel", [1, 2], "caps", max_attempts=3, check_interval=0)

    assert result.success is True
    assert result.successful_requests == 2
    assert result.reference_id == "ref-1"
    assert query.await_count == 3


@pytest.mark.asyncio
async def test_request_image_returns_failure_on_provider_no_response(
    camera_client: CameraClient,
) -> None:
    _set_query_results(
        camera_client,
        [
            {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref-1"}}},
            {
                "errors": [
                    {"message": "alarm-manager.error_no_response_to_request"}
                ],
                "data": {"xSRequestImagesStatus": {"res": "KO"}},
            },
        ],
    )

    result = await camera_client.request_image("installation", "panel", [1], "caps", max_attempts=1, check_interval=0)

    assert result.success is False
    assert result.successful_requests == 0
    assert result.reference_id == "ref-1"


@pytest.mark.asyncio
async def test_request_image_rejects_missing_panel(camera_client: CameraClient) -> None:
    with pytest.raises(MyVerisureError, match="Panel information required"):
        await camera_client.request_image("installation", "", [1], "caps")


@pytest.mark.asyncio
async def test_request_image_rejects_missing_reference_id(camera_client: CameraClient) -> None:
    _set_query_results(
        camera_client,
        [{"data": {"xSRequestImages": {"res": "OK"}}}],
    )

    with pytest.raises(MyVerisureError, match="No reference ID"):
        await camera_client.request_image("installation", "panel", [1], "caps", max_attempts=1, check_interval=0)


@pytest.mark.asyncio
async def test_request_image_returns_failure_after_status_exhaustion(
    camera_client: CameraClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
    _set_query_results(
        camera_client,
        [
            {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref-1"}}},
            {
                "data": {
                    "xSRequestImagesStatus": {
                        "res": "OK",
                        "msg": "alarm-manager.photo-request.processing",
                    }
                }
            },
        ],
    )

    result = await camera_client.request_image("installation", "panel", [1], "caps", max_attempts=1, check_interval=0)

    assert result.success is False
    assert result.successful_requests == 0
    assert result.reference_id == "ref-1"


@pytest.mark.asyncio
async def test_get_images_saves_thumbnail_and_photo(
    camera_client: CameraClient,
) -> None:
    file_manager = camera_client._resolve_file_manager()
    save_image = Mock(return_value=True)
    setattr(file_manager, "save_base64_image", save_image)
    _set_query_results(
        camera_client,
        [
            {
                "data": {
                    "xSGetThumbnail": {
                        "idSignal": "signal-1",
                        "signalType": "16",
                        "deviceAlias": "Front",
                        "timestamp": "2026/08/13 10:20:00",
                        "image": "thumb-data",
                    }
                }
            },
            {
                "data": {
                    "xSGetPhotoImages": {
                        "devices": [
                            {"images": [{"id": "0", "image": "photo-data"}]}
                        ]
                    }
                }
            },
        ],
    )

    result = await camera_client.get_images("installation", "panel", "camera", "zone", "caps")

    assert result["success"] is True
    assert result["images_saved"] == 1
    assert result["thumbnail_saved"] is True
    assert save_image.call_count == 2


@pytest.mark.asyncio
async def test_get_images_rejects_thumbnail_without_signal(
    camera_client: CameraClient,
) -> None:
    _set_query_results(
        camera_client,
        [{"data": {"xSGetThumbnail": {"image": "thumb-data"}}}],
    )

    with pytest.raises(MyVerisureError, match="No idSignal"):
        await camera_client.get_images("installation", "panel", "camera", "zone", "caps")

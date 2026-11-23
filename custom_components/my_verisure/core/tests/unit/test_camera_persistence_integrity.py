"""Camera completion requires distinct images with valid encoded contents.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.api.models.dto.camera_request_image_dto import (
    CameraRequestImageResultDTO,
)
from custom_components.my_verisure.core.application.camera_image_storage import (
    CameraImageStorage,
)
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.models.camera_images import (
    CameraPhotoSet,
    CameraThumbnail,
)
from custom_components.my_verisure.core.application.models.device import Device
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core import file_manager as file_module
from custom_components.my_verisure.core.repositories.implementations import (
    camera_repository_impl,
)
from custom_components.my_verisure.core.session_manager import SessionManager
from custom_components.my_verisure.core.use_cases.implementations import (
    refresh_camera_images_use_case_impl,
)


@pytest.mark.parametrize("encoded", ["", "!!!!", "a", "YWJjZA==!"])
def test_invalid_or_empty_encoded_image_never_creates_a_file(tmp_path, encoded):
    files = FileManager(tmp_path)

    assert files.save_base64_image("cameras/YR01/thumbnail.jpg", encoded) is False
    assert not files.get_file_path("cameras/YR01/thumbnail.jpg").exists()


def _image_bytes(image_format="JPEG"):
    with BytesIO() as stream:
        Image.new("RGB", (2, 2), color=(12, 34, 56)).save(stream, format=image_format)
        return stream.getvalue()


@pytest.mark.parametrize("image_format", ["JPEG", "PNG"])
def test_valid_base64_is_preserved_exactly(tmp_path, image_format):
    files = FileManager(tmp_path)
    image = _image_bytes(image_format)

    assert files.save_base64_image(
        "cameras/YR01/thumbnail.jpg", base64.b64encode(image).decode()
    )
    assert files.get_file_path("cameras/YR01/thumbnail.jpg").read_bytes() == image


@pytest.mark.parametrize("contents", [b"not an image", b"<html>fixture</html>"])
def test_valid_base64_nonimage_does_not_commit_a_camera_file(tmp_path, contents):
    files = FileManager(tmp_path)

    assert (
        files.save_base64_image("photo.jpg", base64.b64encode(contents).decode())
        is False
    )
    assert not files.get_file_path("photo.jpg").exists()


@pytest.mark.parametrize("image_format", ["JPEG", "PNG"])
def test_truncated_image_is_rejected(tmp_path, image_format):
    files = FileManager(tmp_path)
    contents = _image_bytes(image_format)[:-10]

    assert (
        files.save_base64_image("photo.jpg", base64.b64encode(contents).decode())
        is False
    )
    assert not files.get_file_path("photo.jpg").exists()


def test_encoded_size_limit_is_checked_before_decoding(tmp_path, monkeypatch):
    files = FileManager(tmp_path)
    monkeypatch.setattr(file_module, "MAX_CAMERA_IMAGE_BYTES", 3)

    assert files.save_base64_image("photo.jpg", "A" * 100) is False
    assert not files.get_file_path("photo.jpg").exists()


def test_pixel_limit_is_checked_before_loading_image_data(tmp_path, monkeypatch):
    files = FileManager(tmp_path)
    monkeypatch.setattr(file_module, "MAX_CAMERA_IMAGE_PIXELS", 1)

    assert (
        files.save_base64_image("photo.jpg", base64.b64encode(_image_bytes()).decode())
        is False
    )
    assert not files.get_file_path("photo.jpg").exists()


def test_partial_rewrite_invalidates_prior_completion_marker(tmp_path):
    files = FileManager(tmp_path)
    storage = CameraImageStorage(files)
    encoded = base64.b64encode(_image_bytes()).decode()
    thumbnail = CameraThumbnail("123", "16", "Fixture", "timestamp", encoded)
    directory = "2026-11-23_12-00-00"
    complete = storage.save(
        thumbnail,
        CameraPhotoSet([{"id": "0", "image": encoded}]),
        zone_id="YR01",
        timestamp_directory=directory,
    )
    marker = files.get_file_path(f"cameras/YR01/{directory}/.complete")
    assert complete.complete is True
    assert marker.is_file()

    partial = storage.save(
        thumbnail,
        CameraPhotoSet([{"id": "0", "image": "!!!!"}]),
        zone_id="YR01",
        timestamp_directory=directory,
    )

    assert partial.complete is False
    assert not marker.exists()


def test_failed_completion_invalidation_prevents_image_rewrites():
    writer = Mock()
    writer.begin_camera_directory.return_value = False
    storage = CameraImageStorage(writer)

    result = storage.save(
        CameraThumbnail("123", "16", "Fixture", "timestamp", "thumb"),
        CameraPhotoSet([{"id": "0", "image": "photo"}]),
        zone_id="YR01",
        timestamp_directory="2026-11-23_12-00-00",
    )

    assert result.complete is False
    assert result.images_saved == 0
    writer.save_base64_image.assert_not_called()
    writer.mark_camera_directory_complete.assert_not_called()


def test_completion_invalidation_fails_closed_on_filesystem_error(
    tmp_path, monkeypatch
):
    files = FileManager(tmp_path)

    def forbidden_unlink(path, **kwargs):
        raise PermissionError("synthetic permission error")

    monkeypatch.setattr(Path, "unlink", forbidden_unlink)

    assert files.begin_camera_directory("cameras/YR01/timestamp") is False


def test_completion_invalidation_rejects_path_escape(tmp_path):
    files = FileManager(tmp_path)

    assert files.begin_camera_directory("../../outside") is False


@pytest.mark.parametrize("image_ids", [["0", "0"], ["1", ""], ["1", "../escape"]])
def test_invalid_photo_names_fail_before_any_persistence(image_ids):
    writer = Mock()
    storage = CameraImageStorage(writer)

    with pytest.raises(ValueError):
        storage.save(
            CameraThumbnail("123", "16", "Fixture", "timestamp", "thumb"),
            CameraPhotoSet([{"id": value, "image": "photo"} for value in image_ids]),
            zone_id="YR01",
            timestamp_directory="2026-11-23_12-00-00",
        )

    writer.save_base64_image.assert_not_called()
    writer.mark_camera_directory_complete.assert_not_called()


@pytest.mark.parametrize(
    "failure", ["thumbnail", "photo", "duplicate_id", "nonimage", "truncated"]
)
@pytest.mark.asyncio
async def test_malformed_provider_capture_never_publishes_photo_ready(
    tmp_path, failure
):
    files = FileManager(tmp_path)
    session = SessionManager(file_manager=files)
    session.update_credentials(
        "fixture-user", "fixture-password", "fixture-hash", persist=False
    )
    client = CameraClient(session, files)
    encoded = base64.b64encode(_image_bytes()).decode()
    photo = "!!!!" if failure == "photo" else encoded
    if failure == "nonimage":
        photo = base64.b64encode(b"not an image").decode()
    elif failure == "truncated":
        photo = base64.b64encode(_image_bytes()[:-10]).decode()
    images = [{"id": "0", "image": photo}]
    if failure == "duplicate_id":
        images.append({"id": "0", "image": encoded})
    client._execute_query_direct = AsyncMock(
        side_effect=[
            {
                "data": {
                    "xSGetThumbnail": {
                        "idSignal": "123",
                        "signalType": "16",
                        "deviceAlias": "Fixture",
                        "deviceCode": "YR01",
                        "timestamp": "2026-11-23 12:00:00",
                        "image": "!!!!" if failure == "thumbnail" else encoded,
                    }
                }
            },
            {
                "data": {
                    "xSGetPhotoImages": {"devices": [{"code": "1", "images": images}]}
                }
            },
        ]
    )
    client.request_image = AsyncMock(
        return_value=CameraRequestImageResultDTO(True, 1, "reference", "123")
    )
    installation = SimpleNamespace(
        get_installation_services=AsyncMock(
            return_value=SimpleNamespace(
                installation=SimpleNamespace(
                    panel="fixture-panel",
                    capabilities="fixture-capabilities",
                    devices=[
                        Device(
                            "fixture-id", "1", "Fixture", "YR", "", True, "CAM", True
                        )
                    ],
                )
            )
        )
    )
    use_case = refresh_camera_images_use_case_impl.RefreshCameraImagesUseCaseImpl(
        camera_repository_impl.CameraRepositoryImpl(client), installation
    )
    callback = Mock()
    use_case.set_photo_committed_callback(callback)

    if failure == "duplicate_id":
        with pytest.raises(MyVerisureError):
            await use_case.refresh_camera_images("fixture-installation")
    else:
        result = await use_case.refresh_camera_images("fixture-installation")
        assert result.successful_refreshes == 0
        assert result.failed_refreshes == 1

    callback.assert_not_called()
    assert not list(files.get_data_directory().rglob(".complete"))
    assert client._execute_query_direct.await_count == 2

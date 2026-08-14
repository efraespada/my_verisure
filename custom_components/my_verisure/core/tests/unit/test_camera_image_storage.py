"""Contract tests for camera image persistence policy."""

from unittest.mock import Mock

from custom_components.my_verisure.core.application.camera_image_response_interpreter import (
    CameraPhotoSet,
    CameraThumbnail,
)
from custom_components.my_verisure.core.application.camera_image_storage import (
    CameraImageStorage,
)


def test_storage_writes_thumbnail_and_numbered_photos() -> None:
    writer = Mock()
    writer.save_base64_image.return_value = True
    storage = CameraImageStorage(writer)

    result = storage.save(
        CameraThumbnail("signal", "16", "Front", "timestamp", "thumb"),
        CameraPhotoSet(
            [
                {"id": "0", "image": "photo-0"},
                {"id": "3", "image": "photo-3"},
            ]
        ),
        zone_id="YR01",
        timestamp_directory="2026-08-14_10-00-00",
    )

    assert result.thumbnail_saved is True
    assert result.images_saved == 2
    assert result.total_images == 2
    assert [call.args for call in writer.save_base64_image.call_args_list] == [
        ("cameras/YR01/2026-08-14_10-00-00/thumbnail.jpg", "thumb"),
        ("cameras/YR01/2026-08-14_10-00-00/1.jpg", "photo-0"),
        ("cameras/YR01/2026-08-14_10-00-00/imagen_3.jpg", "photo-3"),
    ]


def test_storage_handles_photos_without_thumbnail() -> None:
    writer = Mock()
    writer.save_base64_image.return_value = True
    storage = CameraImageStorage(writer)

    result = storage.save(
        CameraThumbnail("signal", "16", "Front", "timestamp", ""),
        CameraPhotoSet([{"id": "1", "image": "photo"}]),
        zone_id="YR01",
        timestamp_directory="fallback",
    )

    assert result.thumbnail_saved is False
    assert result.images_saved == 1
    assert writer.save_base64_image.call_args.args == (
        "cameras/YR01/fallback/2.jpg",
        "photo",
    )

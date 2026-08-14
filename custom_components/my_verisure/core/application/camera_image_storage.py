"""Application boundary for persisting camera images."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .camera_image_response_interpreter import CameraPhotoSet, CameraThumbnail


class CameraImageWriter(Protocol):
    """Port for writing encoded camera images."""

    def save_base64_image(self, filepath: str, base64_content: str) -> bool:
        """Persist one encoded image and report whether it was written."""
        ...


@dataclass(frozen=True)
class CameraImageStorageResult:
    """Persistence outcome for one camera image response."""

    thumbnail_saved: bool
    images_saved: int
    total_images: int


class CameraImageStorage:
    """Persist typed camera images without depending on a filesystem adapter."""

    def __init__(self, writer: CameraImageWriter) -> None:
        self._writer = writer

    def save(
        self,
        thumbnail: CameraThumbnail,
        photos: CameraPhotoSet,
        *,
        zone_id: str,
        timestamp_directory: str,
    ) -> CameraImageStorageResult:
        """Save the thumbnail and additional photos under one camera directory."""
        device_directory = f"cameras/{zone_id}/{timestamp_directory}"
        thumbnail_saved = False
        if thumbnail.image:
            thumbnail_saved = self._writer.save_base64_image(
                f"{device_directory}/thumbnail.jpg",
                thumbnail.image,
            )

        images_saved = 0
        for image in photos.images:
            image_data = image["image"]
            if not image_data:
                continue
            image_id = image["id"]
            filename = self._image_filename(image_id)
            if self._writer.save_base64_image(
                f"{device_directory}/{filename}",
                image_data,
            ):
                images_saved += 1

        return CameraImageStorageResult(
            thumbnail_saved=thumbnail_saved,
            images_saved=images_saved,
            total_images=len(photos.images),
        )

    @staticmethod
    def _image_filename(image_id: str) -> str:
        numbered_names = {"0": "1.jpg", "1": "2.jpg", "2": "3.jpg"}
        return numbered_names.get(image_id, f"imagen_{image_id}.jpg")

"""Application boundary for persisting camera images."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models.camera_images import CameraPhotoSet, CameraThumbnail


class CameraImageWriter(Protocol):
    """Port for writing encoded camera images."""

    def save_base64_image(self, filepath: str, base64_content: str) -> bool:
        """Persist one encoded image and report whether it was written."""
        ...

    def mark_camera_directory_complete(self, directory: str) -> bool:
        """Commit a camera directory after every expected image is persisted."""
        ...


@dataclass(frozen=True)
class CameraImageStorageResult:
    """Persistence outcome for one camera image response."""

    thumbnail_saved: bool
    images_saved: int
    total_images: int
    complete: bool


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
        device_directory = (
            "cameras/"
            f"{self._safe_component(zone_id)}/"
            f"{self._safe_component(timestamp_directory)}"
        )
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

        complete = (
            thumbnail_saved
            and bool(photos.images)
            and images_saved == len(photos.images)
        )
        if complete:
            complete = bool(
                self._writer.mark_camera_directory_complete(device_directory)
            )

        return CameraImageStorageResult(
            thumbnail_saved=thumbnail_saved,
            images_saved=images_saved,
            total_images=len(photos.images),
            complete=complete,
        )

    @staticmethod
    def _safe_component(value: str) -> str:
        """Accept only one non-empty, non-traversing provider path component."""
        if (
            not isinstance(value, str)
            or not value.strip()
            or value in {".", ".."}
            or "/" in value
            or "\\" in value
        ):
            raise ValueError("unsafe camera path component")
        return value

    @classmethod
    def _image_filename(cls, image_id: str) -> str:
        numbered_names = {"0": "1.jpg", "1": "2.jpg", "2": "3.jpg"}
        safe_id = cls._safe_component(image_id)
        return numbered_names.get(safe_id, f"imagen_{safe_id}.jpg")

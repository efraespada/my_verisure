"""Application boundary for coordinator refresh side effects."""

from __future__ import annotations

import logging
from typing import Any, Protocol

from .coordinator_snapshot_store import CoordinatorSnapshotStore

_LOGGER = logging.getLogger(__name__)


class CoordinatorDataPublisher(Protocol):
    """Port for publishing data through the Home Assistant coordinator."""

    def __call__(self, data: dict[str, Any]) -> None:
        """Publish the refreshed data."""


class DummyCameraImageCreator(Protocol):
    """Port for creating camera placeholders after a refresh."""

    async def create_dummy_camera_images(self, installation_id: str) -> Any:
        """Create dummy camera images."""


class CoordinatorRefreshEffects:
    """Apply non-domain effects after a successful snapshot refresh."""

    def __init__(
        self,
        snapshot_store: CoordinatorSnapshotStore,
        publisher: CoordinatorDataPublisher,
        dummy_camera_creator: DummyCameraImageCreator | None = None,
    ) -> None:
        self._snapshot_store = snapshot_store
        self._publisher = publisher
        self._dummy_camera_creator = dummy_camera_creator

    async def apply(
        self,
        snapshot: dict[str, Any],
        installation_id: str,
        *,
        create_dummy_images: bool,
    ) -> None:
        """Publish and persist a snapshot, then optionally create placeholders."""
        try:
            self._publisher(snapshot)
        except Exception as error:  # HA publisher boundary must not hide data
            _LOGGER.error("Failed to publish coordinator data: %s", error)

        saved = await self._snapshot_store.save(snapshot)
        if not saved:
            _LOGGER.error("Failed to save coordinator data")

        if create_dummy_images and self._dummy_camera_creator is not None:
            try:
                await self._dummy_camera_creator.create_dummy_camera_images(
                    installation_id
                )
            except Exception as error:
                _LOGGER.error("Failed to create dummy camera images: %s", error)

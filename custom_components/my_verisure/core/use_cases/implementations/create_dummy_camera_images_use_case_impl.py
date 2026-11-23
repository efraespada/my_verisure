"""Select requested cameras and delegate local placeholder storage.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from ...application.camera_devices import camera_devices, camera_identifier
from ...application.camera_placeholders import CameraPlaceholderStore
from ...application.exceptions import MyVerisureError
from ...application.models.camera_refresh import CameraRefresh
from ...repositories.interfaces.installation_repository import InstallationRepository
from ..interfaces.create_dummy_camera_images_use_case import (
    CreateDummyCameraImagesUseCase,
)


class CreateDummyCameraImagesUseCaseImpl(CreateDummyCameraImagesUseCase):
    """Keep periodic HA refreshes local; support explicit CLI camera discovery."""

    def __init__(
        self,
        installation_repository: InstallationRepository,
        placeholder_store: CameraPlaceholderStore,
    ) -> None:
        self.installation_repository = installation_repository
        self.placeholder_store = placeholder_store

    async def create_dummy_camera_images(
        self,
        installation_id: str,
        *,
        camera_identifiers: tuple[str, ...] | None = None,
    ) -> CameraRefresh:
        """Use supplied snapshot cameras, or discover them for an explicit action."""
        try:
            if camera_identifiers is None:
                detailed = await self.installation_repository.get_installation_services(
                    installation_id
                )
                camera_identifiers = tuple(
                    camera_identifier(device)
                    for device in camera_devices(detailed.installation.devices)
                )
            return await self.placeholder_store.ensure_placeholders(camera_identifiers)
        except MyVerisureError:
            raise
        except Exception:
            raise MyVerisureError("Dummy camera image creation failed") from None

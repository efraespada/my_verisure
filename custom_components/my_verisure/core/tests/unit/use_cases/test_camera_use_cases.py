"""Unit tests for current camera image use-case contracts."""

from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ....application.models.camera_request_image import CameraRequestImageResult
from ....application.models.camera_refresh import CameraRefresh
from ....application.models.device import Device
from ....application.models.installation import DetailedInstallation, InstallationData
from ....file_manager import FileManager
from ....application.exceptions import MyVerisureError
from ....repositories.interfaces.camera_repository import CameraRepository
from ....repositories.interfaces.installation_repository import InstallationRepository
from ....use_cases.implementations.create_dummy_camera_images_use_case_impl import CreateDummyCameraImagesUseCaseImpl
from ....use_cases.implementations.refresh_camera_images_use_case_impl import RefreshCameraImagesUseCaseImpl
from ....use_cases.interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase


def _installation(devices, *, panel: str | None = "PROTOCOL", capabilities: str | None = "caps"):
    return DetailedInstallation(
        installation=InstallationData(
            numinst="12345", role="OWNER", alias="Home", status="OP",
            panel=cast(str, panel), sim="sim", instIbs="ibs", services=[],
            configRepoUser=None, capabilities=cast(str, capabilities), devices=devices,
        ),
        language="es",
    )


def _camera():
    return Device("id", "1", "Front", "YR", "", True, "CAM", True)


@pytest.fixture
def installation_repository():
    repository = Mock(spec=InstallationRepository)
    repository.get_installation_services = AsyncMock(return_value=_installation([_camera()]))
    return repository


@pytest.mark.asyncio
async def test_refresh_camera_images_success(installation_repository):
    camera = Mock(spec=CameraRepository)
    camera.request_image = AsyncMock(return_value=CameraRequestImageResult(True, 1, "ref"))
    camera.get_images = AsyncMock(return_value={"success": True, "images_saved": 2})
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation_repository)

    with patch("my_verisure.core.use_cases.implementations.refresh_camera_images_use_case_impl.asyncio.sleep", new_callable=AsyncMock):
        result = await use_case.refresh_camera_images("12345")

    assert isinstance(result, CameraRefresh)
    assert result.total_cameras == 1
    assert result.successful_refreshes == 1
    assert result.refresh_data[0].num_images == 2


@pytest.mark.asyncio
async def test_refresh_camera_images_does_not_count_unpersisted_images(
    installation_repository,
):
    camera = Mock(spec=CameraRepository)
    camera.request_image = AsyncMock(return_value=CameraRequestImageResult(True, 1, "ref"))
    camera.get_images = AsyncMock(return_value={"success": False, "images_saved": 2})
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation_repository)

    with patch("my_verisure.core.use_cases.implementations.refresh_camera_images_use_case_impl.asyncio.sleep", new_callable=AsyncMock):
        result = await use_case.refresh_camera_images("12345")

    assert result.total_cameras == 1
    assert result.successful_refreshes == 0
    assert result.failed_refreshes == 1


@pytest.mark.asyncio
async def test_refresh_camera_images_installation_error():
    installation = Mock(spec=InstallationRepository)
    installation.get_installation_services = AsyncMock(
        side_effect=MyVerisureError("missing")
    )
    camera = Mock(spec=CameraRepository)
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation)

    with pytest.raises(MyVerisureError, match="missing"):
        await use_case.refresh_camera_images("12345")


@pytest.mark.asyncio
async def test_refresh_camera_images_unexpected_installation_error_is_terminal():
    installation = Mock(spec=InstallationRepository)
    installation.get_installation_services = AsyncMock(
        side_effect=RuntimeError("unexpected")
    )
    camera = Mock(spec=CameraRepository)
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation)

    with pytest.raises(MyVerisureError, match="Camera image refresh failed"):
        await use_case.refresh_camera_images("12345")


@pytest.mark.asyncio
async def test_refresh_camera_images_rejects_missing_installation_context(
    installation_repository,
):
    installation_repository.get_installation_services.return_value = _installation(
        [_camera()], panel=None, capabilities=None
    )
    camera = Mock(spec=CameraRepository)
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation_repository)

    with pytest.raises(MyVerisureError, match="Installation context unavailable"):
        await use_case.refresh_camera_images("12345")


@pytest.mark.asyncio
async def test_refresh_camera_images_camera_error(installation_repository):
    camera = Mock(spec=CameraRepository)
    camera.request_image = AsyncMock(side_effect=RuntimeError("camera"))
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation_repository)

    result = await use_case.refresh_camera_images("12345")

    assert result.total_cameras == 1
    assert result.successful_refreshes == 0
    assert result.failed_refreshes == 1




@pytest.mark.asyncio
async def test_create_dummy_propagates_installation_domain_error(installation_repository):
    installation_repository.get_installation_services.side_effect = MyVerisureError("missing")
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository, Mock())

    with pytest.raises(MyVerisureError, match="missing"):
        await use_case.create_dummy_camera_images("12345")


@pytest.mark.asyncio
async def test_create_dummy_rejects_zero_persisted_images(
    installation_repository, tmp_path
):
    file_manager = FileManager(tmp_path)
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository, file_manager)
    use_case._create_dummy_images = Mock(return_value=0)

    with pytest.raises(MyVerisureError, match="Dummy camera image creation failed"):
        await use_case.create_dummy_camera_images("12345")

    assert not list(tmp_path.rglob("*.staging"))

def test_create_dummy_implements_interface(installation_repository):
    assert isinstance(
        CreateDummyCameraImagesUseCaseImpl(installation_repository, Mock()),
        CreateDummyCameraImagesUseCase,
    )


def test_create_dummy_cleans_partial_directory_on_image_failure(tmp_path):
    use_case = CreateDummyCameraImagesUseCaseImpl(Mock(), Mock())
    directory = tmp_path / "camera" / "timestamp"
    directory.mkdir(parents=True)
    image = Mock()
    image.save.side_effect = [None, OSError("disk full")]

    with patch(
        "custom_components.my_verisure.core.use_cases.implementations.create_dummy_camera_images_use_case_impl.Image.new",
        return_value=image,
    ):
        assert use_case._create_dummy_images(str(directory)) == 0

    assert not directory.exists()


@pytest.mark.asyncio
async def test_create_dummy_without_cameras_returns_empty(installation_repository):
    installation_repository.get_installation_services.return_value = _installation([])
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository, Mock())

    result = await use_case.create_dummy_camera_images("12345")

    assert result.total_cameras == 0
    assert result.refresh_data == []

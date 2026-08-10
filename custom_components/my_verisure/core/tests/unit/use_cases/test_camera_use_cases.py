"""Unit tests for current camera image use-case contracts."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ....api.models.domain.camera_request_image import CameraRequestImageResult
from ....api.models.domain.camera_refresh import CameraRefresh
from ....api.models.domain.device import Device
from ....api.models.domain.installation import DetailedInstallation, InstallationData
from ....repositories.interfaces.camera_repository import CameraRepository
from ....repositories.interfaces.installation_repository import InstallationRepository
from ....use_cases.implementations.create_dummy_camera_images_use_case_impl import CreateDummyCameraImagesUseCaseImpl
from ....use_cases.implementations.refresh_camera_images_use_case_impl import RefreshCameraImagesUseCaseImpl
from ....use_cases.interfaces.create_dummy_camera_images_use_case import CreateDummyCameraImagesUseCase


def _installation(devices):
    return DetailedInstallation(
        installation=InstallationData(
            numinst="12345", role="OWNER", alias="Home", status="OP",
            panel="PROTOCOL", sim="sim", instIbs="ibs", services=[],
            configRepoUser=None, capabilities="caps", devices=devices,
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
    camera.get_images = AsyncMock(return_value={"images_saved": 2})
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation_repository)

    with patch("my_verisure.core.use_cases.implementations.refresh_camera_images_use_case_impl.asyncio.sleep", new_callable=AsyncMock):
        result = await use_case.refresh_camera_images("12345")

    assert isinstance(result, CameraRefresh)
    assert result.total_cameras == 1
    assert result.successful_refreshes == 1
    assert result.refresh_data[0].num_images == 2


@pytest.mark.asyncio
async def test_refresh_camera_images_installation_error():
    installation = Mock(spec=InstallationRepository)
    installation.get_installation_services = AsyncMock(side_effect=RuntimeError("missing"))
    camera = Mock(spec=CameraRepository)
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation)

    result = await use_case.refresh_camera_images("12345")

    assert result.total_cameras == 0
    assert result.failed_refreshes == 0


@pytest.mark.asyncio
async def test_refresh_camera_images_camera_error(installation_repository):
    camera = Mock(spec=CameraRepository)
    camera.request_image = AsyncMock(side_effect=RuntimeError("camera"))
    use_case = RefreshCameraImagesUseCaseImpl(camera, installation_repository)

    result = await use_case.refresh_camera_images("12345")

    assert result.total_cameras == 1
    assert result.successful_refreshes == 0
    assert result.failed_refreshes == 1


def test_create_dummy_implements_interface(installation_repository):
    assert isinstance(CreateDummyCameraImagesUseCaseImpl(installation_repository), CreateDummyCameraImagesUseCase)


@pytest.mark.asyncio
async def test_create_dummy_without_cameras_returns_empty(installation_repository):
    installation_repository.get_installation_services.return_value = _installation([])
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository)

    result = await use_case.create_dummy_camera_images("12345")

    assert result.total_cameras == 0
    assert result.refresh_data == []

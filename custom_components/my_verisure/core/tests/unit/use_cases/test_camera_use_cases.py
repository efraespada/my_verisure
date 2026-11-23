"""Unit tests for current camera image use-case contracts."""

from typing import cast
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ....application.models.camera_request_image import CameraRequestImageResult
from ....application.models.camera_refresh import CameraRefresh
from ....application.models.device import Device
from ....application.models.installation import DetailedInstallation, InstallationData
from ....file_manager import FileManager
from ....camera_placeholder_store import LocalCameraPlaceholderStore
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
    store = LocalCameraPlaceholderStore(file_manager)
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository, store)
    store._write_images = Mock(side_effect=OSError("disk full"))

    with pytest.raises(MyVerisureError, match="Dummy camera image creation failed"):
        await use_case.create_dummy_camera_images("12345")

    assert not list(tmp_path.rglob("*.staging"))

def test_create_dummy_implements_interface(installation_repository):
    assert isinstance(
        CreateDummyCameraImagesUseCaseImpl(installation_repository, Mock()),
        CreateDummyCameraImagesUseCase,
    )


@pytest.mark.asyncio
async def test_create_dummy_cleans_partial_directory_on_image_failure(tmp_path):
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    with patch.object(store, "_write_images", side_effect=OSError("disk full")):
        with pytest.raises(MyVerisureError, match="Dummy camera image creation failed"):
            await store.ensure_placeholders(("YR01",))
    assert not list(tmp_path.rglob("*.staging"))
    assert not list(tmp_path.rglob(".complete"))


@pytest.mark.asyncio
async def test_create_dummy_without_cameras_returns_empty(installation_repository, tmp_path):
    installation_repository.get_installation_services.return_value = _installation([])
    use_case = CreateDummyCameraImagesUseCaseImpl(
        installation_repository, LocalCameraPlaceholderStore(FileManager(tmp_path))
    )

    result = await use_case.create_dummy_camera_images("12345")

    assert result.total_cameras == 0
    assert result.refresh_data == []


@pytest.mark.asyncio
async def test_create_dummy_reuses_supplied_cameras_without_provider_reads(
    installation_repository, tmp_path
):
    installation_repository.get_installation_services.side_effect = AssertionError(
        "No additional provider requests are allowed"
    )
    store = LocalCameraPlaceholderStore(FileManager(tmp_path))
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository, store)

    result = await use_case.create_dummy_camera_images(
        "12345", camera_identifiers=("YR01",)
    )
    repeated = await use_case.create_dummy_camera_images(
        "12345", camera_identifiers=("YR01",)
    )

    assert result.successful_refreshes == repeated.successful_refreshes == 1
    assert repeated.refresh_data[0].num_images == 0
    installation_repository.get_installation_services.assert_not_awaited()
    assert len(list(tmp_path.rglob("thumbnail.jpg"))) == 1


@pytest.mark.asyncio
async def test_create_dummy_sanitizes_unexpected_storage_failure(installation_repository):
    store = Mock(ensure_placeholders=AsyncMock(side_effect=OSError("synthetic-sensitive")))
    use_case = CreateDummyCameraImagesUseCaseImpl(installation_repository, store)
    with pytest.raises(MyVerisureError, match="Dummy camera image creation failed") as error:
        await use_case.create_dummy_camera_images("12345", camera_identifiers=())
    assert "synthetic-sensitive" not in str(error.value)

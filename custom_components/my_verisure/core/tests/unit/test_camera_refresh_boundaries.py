"""Exercise camera refresh limits through real application/adapter boundaries.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.api.camera_client import CameraClient
from custom_components.my_verisure.core.application.exceptions import MyVerisureError
from custom_components.my_verisure.core.application.models.device import Device
from custom_components.my_verisure.core.application.models.installation import (
    DetailedInstallation,
    InstallationData,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.repositories.implementations.camera_repository_impl import CameraRepositoryImpl
from custom_components.my_verisure.core.session_manager import SessionManager
from custom_components.my_verisure.core.use_cases.implementations.refresh_camera_images_use_case_impl import RefreshCameraImagesUseCaseImpl


def _installation():
    repository = Mock()
    repository.get_installation_services = AsyncMock(return_value=DetailedInstallation(
        installation=InstallationData(
            numinst="12345", role="OWNER", alias="Home", status="OP",
            panel="panel", sim="sim", instIbs="ibs", services=[],
            configRepoUser=None, capabilities="caps",
            devices=[
                Device("a", "1", "Front", "YR", "", True, "CAM", True),
                Device("b", "2", "Back", "YR", "", True, "CAM", True),
            ],
        ), language="es",
    ))
    return repository


@pytest.mark.asyncio
async def test_polling_budget_reaches_transport_without_extra_requests(tmp_path, monkeypatch):
    manager = FileManager(tmp_path)
    session = SessionManager(file_manager=manager)
    session.hash_token, session.username, session.password = "hash", "user", "password"
    client = CameraClient(session, manager)

    async def query(document, variables, headers):
        if "mutation RequestImages(" in document:
            return {"data": {"xSRequestImages": {"res": "OK", "referenceId": "ref"}}}
        assert "query RequestImagesStatus(" in document
        return {"data": {"xSRequestImagesStatus": {
            "res": "OK", "msg": "alarm-manager.photo-request.processing",
            "numinst": None, "status": None,
        }}}

    transport = AsyncMock(side_effect=query)
    monkeypatch.setattr(client, "_execute_query_direct", transport)
    sleep = AsyncMock()
    monkeypatch.setattr("asyncio.sleep", sleep)
    installation = _installation()
    installation.get_installation_services.return_value.installation.devices.pop()
    use_case = RefreshCameraImagesUseCaseImpl(CameraRepositoryImpl(client), installation)

    result = await use_case.refresh_camera_images("12345", max_attempts=3, check_interval=17)

    assert result.failed_refreshes == 1
    assert transport.await_count == 4  # one mutation and exactly three status reads
    assert [call.args[0] for call in sleep.await_args_list] == [17, 17]


@pytest.mark.asyncio
async def test_selected_camera_never_requests_other_cameras():
    camera = Mock()
    camera.request_image = AsyncMock(return_value=Mock(successful_requests=0))
    use_case = RefreshCameraImagesUseCaseImpl(camera, _installation())

    result = await use_case.refresh_camera_images("12345", camera_identifier="YR02")

    assert result.total_cameras == 1
    assert camera.request_image.await_count == 1
    assert camera.request_image.await_args.kwargs["devices"] == [2]


@pytest.mark.asyncio
async def test_unknown_camera_selection_does_not_fall_back_to_all_cameras():
    camera = Mock()
    camera.request_image = AsyncMock()
    use_case = RefreshCameraImagesUseCaseImpl(camera, _installation())

    with pytest.raises(MyVerisureError, match="Selected camera unavailable"):
        await use_case.refresh_camera_images("12345", camera_identifier="YR99")

    camera.request_image.assert_not_awaited()

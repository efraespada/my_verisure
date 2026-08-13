"""Tests for the installation devices use-case contract."""

from unittest.mock import AsyncMock, Mock

import pytest

from ...api.models.domain.device import Device, DeviceList
from ...api.models.domain.installation import DetailedInstallation, InstallationData
from ...repositories.interfaces.installation_repository import InstallationRepository
from ...use_cases.implementations.get_installation_devices_use_case_impl import (
    GetInstallationDevicesUseCaseImpl,
)


@pytest.mark.asyncio
async def test_get_installation_devices_returns_device_list() -> None:
    repository = Mock(spec=InstallationRepository)
    repository.get_installation_services = AsyncMock(
        return_value=DetailedInstallation(
            installation=InstallationData(
                numinst="1",
                role="owner",
                alias="Home",
                status="OK",
                panel="panel",
                sim="sim",
                instIbs="ibs",
                services=[],
                devices=[
                    Device(
                        id="d1",
                        code="001",
                        name="Door",
                        type="DOOR",
                        subtype="contact",
                        remote_use=True,
                        id_service="service",
                        is_active=True,
                    )
                ],
            ),
            language="en",
        )
    )

    result = await GetInstallationDevicesUseCaseImpl(
        repository
    ).get_installation_devices("1")

    assert isinstance(result, DeviceList)
    assert [device.id for device in result.devices] == ["d1"]
    repository.get_installation_services.assert_awaited_once_with(
        installation_id="1",
        force_refresh=False,
    )

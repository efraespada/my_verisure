"""Unit tests for current installation use-case contracts."""

from unittest.mock import AsyncMock, Mock

import pytest

from ....api.exceptions import MyVerisureError
from ....api.models.domain.installation import DetailedInstallation, Installation, InstallationData
from ....repositories.interfaces.installation_repository import InstallationRepository
from ....use_cases.implementations.installation_use_case_impl import InstallationUseCaseImpl
from ....use_cases.interfaces.installation_use_case import InstallationUseCase


@pytest.fixture
def repository():
    value = Mock(spec=InstallationRepository)
    value.get_installations = AsyncMock()
    value.get_installation_services = AsyncMock()
    return value


@pytest.fixture
def use_case(repository):
    return InstallationUseCaseImpl(repository)


def test_implements_interface(use_case):
    assert isinstance(use_case, InstallationUseCase)


@pytest.mark.asyncio
async def test_get_installations_delegates(use_case, repository):
    expected = [Installation("1", "Home", "panel", "residential", "A", "B", "street", "city", "000", "province", "a@b", "phone")]
    repository.get_installations.return_value = expected

    assert await use_case.get_installations() == expected
    repository.get_installations.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_get_installations_propagates_error(use_case, repository):
    repository.get_installations.side_effect = MyVerisureError("connection")
    with pytest.raises(MyVerisureError, match="connection"):
        await use_case.get_installations()


@pytest.mark.asyncio
async def test_get_services_delegates_force_refresh(use_case, repository):
    expected = DetailedInstallation(
        InstallationData("1", "owner", "Home", "OP", "panel", "sim", "ibs", [], []),
        "es",
    )
    repository.get_installation_services.return_value = expected

    result = await use_case.get_installation_services("1", force_refresh=True)

    assert result == expected
    repository.get_installation_services.assert_awaited_once_with("1", True)


@pytest.mark.asyncio
async def test_get_services_propagates_error(use_case, repository):
    repository.get_installation_services.side_effect = MyVerisureError("not found")
    with pytest.raises(MyVerisureError, match="not found"):
        await use_case.get_installation_services("1")

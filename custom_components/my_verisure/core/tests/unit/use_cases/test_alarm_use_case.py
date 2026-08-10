"""Unit tests for the current alarm use-case contract."""

from unittest.mock import AsyncMock, Mock

import pytest

from ....api.exceptions import MyVerisureError
from ....api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult
from ....api.models.domain.installation import DetailedInstallation, InstallationData
from ....repositories.interfaces.alarm_repository import AlarmRepository
from ....repositories.interfaces.installation_repository import InstallationRepository
from ....use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
from ....use_cases.interfaces.alarm_use_case import AlarmUseCase


@pytest.fixture
def alarm_dependencies():
    alarm = Mock(spec=AlarmRepository)
    alarm.get_alarm_status = AsyncMock()
    alarm.arm_away = AsyncMock()
    alarm.arm_home = AsyncMock()
    alarm.arm_night = AsyncMock()
    alarm.disarm_panel = AsyncMock()

    installation = Mock(spec=InstallationRepository)
    installation.get_installation_services = AsyncMock(return_value=DetailedInstallation(
        installation=InstallationData(
            numinst="12345", role="OWNER", alias="Home", status="OP",
            panel="PROTOCOL", sim="sim", instIbs="ibs", services=[],
            configRepoUser=None, capabilities="caps", devices=[],
        ),
        language="es",
    ))
    return alarm, installation


@pytest.fixture
def alarm_use_case(alarm_dependencies):
    alarm, installation = alarm_dependencies
    return AlarmUseCaseImpl(alarm, installation)


def test_implements_interface(alarm_use_case):
    assert isinstance(alarm_use_case, AlarmUseCase)


@pytest.mark.asyncio
async def test_get_alarm_status_resolves_installation_context(alarm_use_case, alarm_dependencies):
    alarm, _ = alarm_dependencies
    expected = AlarmStatus(success=True, message="ok", status="ARMED", numinst="12345")
    alarm.get_alarm_status.return_value = expected

    result = await alarm_use_case.get_alarm_status("12345")

    assert result == expected
    alarm.get_alarm_status.assert_awaited_once_with("12345", "PROTOCOL", "caps")


@pytest.mark.parametrize(
    ("method", "repository_method"),
    [("arm_away", "arm_away"), ("arm_home", "arm_home"), ("arm_night", "arm_night")],
)
@pytest.mark.asyncio
async def test_arm_modes_use_current_repository_contract(
    alarm_use_case, alarm_dependencies, method, repository_method
):
    alarm, _ = alarm_dependencies
    expected = ArmResult(success=True, message="armed")
    getattr(alarm, repository_method).return_value = expected

    result = await getattr(alarm_use_case, method)("12345")

    assert result == expected
    getattr(alarm, repository_method).assert_awaited_once_with(
        installation_id="12345", panel="PROTOCOL", capabilities="caps",
        auto_arm_perimeter_with_internal=False,
    ) if method != "arm_home" else getattr(alarm, repository_method).assert_awaited_once_with(
        installation_id="12345", panel="PROTOCOL", capabilities="caps"
    )


@pytest.mark.asyncio
async def test_disarm_uses_current_repository_contract(alarm_use_case, alarm_dependencies):
    alarm, _ = alarm_dependencies
    expected = DisarmResult(success=True, message="disarmed")
    alarm.disarm_panel.return_value = expected

    result = await alarm_use_case.disarm("12345")

    assert result == expected
    alarm.disarm_panel.assert_awaited_once_with("12345", "PROTOCOL", "caps")


@pytest.mark.asyncio
async def test_repository_errors_are_propagated(alarm_use_case, alarm_dependencies):
    alarm, _ = alarm_dependencies
    alarm.arm_away.side_effect = MyVerisureError("API failure")

    with pytest.raises(MyVerisureError, match="API failure"):
        await alarm_use_case.arm_away("12345")

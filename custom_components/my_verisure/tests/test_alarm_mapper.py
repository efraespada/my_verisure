"""Contract tests for alarm DTO adapters."""

from custom_components.my_verisure.core.api.mappers.alarm_mapper import (
    alarm_status_from_dto,
    alarm_status_to_dto,
    arm_result_from_dto,
    arm_result_to_dto,
    disarm_result_from_dto,
    disarm_result_to_dto,
)
from custom_components.my_verisure.core.api.models.domain.alarm import (
    AlarmStatus,
    ArmResult,
    DisarmResult,
)
from custom_components.my_verisure.core.api.models.dto.alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    DisarmResultDTO,
)


def test_arm_result_mapping_round_trip() -> None:
    dto = ArmResultDTO("OK", "armed", "ref")
    value = arm_result_from_dto(dto)
    assert value == ArmResult(True, "armed", "ref")
    assert arm_result_to_dto(value) == dto


def test_disarm_result_mapping_round_trip() -> None:
    dto = DisarmResultDTO("KO", "failed")
    value = disarm_result_from_dto(dto)
    assert value == DisarmResult(False, "failed")
    assert disarm_result_to_dto(value) == dto


def test_alarm_status_mapping_round_trip() -> None:
    dto = AlarmStatusDTO(
        "OK", "No alarm", "OK", "123", "No alarm", "2026-01-01", False
    )
    value = alarm_status_from_dto(dto)
    assert value == AlarmStatus(
        True, "No alarm", "OK", "123", "No alarm", "2026-01-01", False
    )
    assert alarm_status_to_dto(value) == dto

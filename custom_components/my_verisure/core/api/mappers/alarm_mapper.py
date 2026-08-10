"""Mappings between alarm transport DTOs and domain values."""

from ..models.domain.alarm import (
    AlarmStatus,
    ArmResult,
    ArmStatus,
    CheckAlarm,
    DisarmResult,
    DisarmStatus,
)
from ..models.dto.alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    ArmStatusDTO,
    CheckAlarmDTO,
    DisarmResultDTO,
    DisarmStatusDTO,
)


def arm_result_from_dto(dto: ArmResultDTO) -> ArmResult:
    return ArmResult(dto.res == "OK", dto.msg or "", dto.reference_id)


def arm_result_to_dto(value: ArmResult) -> ArmResultDTO:
    return ArmResultDTO("OK" if value.success else "KO", value.message, value.reference_id)


def disarm_result_from_dto(dto: DisarmResultDTO) -> DisarmResult:
    return DisarmResult(dto.res == "OK", dto.msg or "", dto.reference_id)


def disarm_result_to_dto(value: DisarmResult) -> DisarmResultDTO:
    return DisarmResultDTO("OK" if value.success else "KO", value.message, value.reference_id)


def alarm_status_from_dto(dto: AlarmStatusDTO) -> AlarmStatus:
    return AlarmStatus(
        success=dto.res == "OK",
        message=dto.msg or "",
        status=dto.status,
        numinst=dto.numinst,
        protom_response=dto.protom_response,
        protom_response_date=dto.protom_response_date,
        forced_armed=dto.forced_armed,
    )


def alarm_status_to_dto(value: AlarmStatus) -> AlarmStatusDTO:
    return AlarmStatusDTO(
        "OK" if value.success else "KO",
        value.message,
        value.status,
        value.numinst,
        value.protom_response,
        value.protom_response_date,
        value.forced_armed,
    )


def arm_status_from_dto(dto: ArmStatusDTO) -> ArmStatus:
    return ArmStatus(
        success=dto.res == "OK",
        message=dto.msg or "",
        status=dto.status,
        protom_response=dto.protom_response,
        protom_response_date=dto.protom_response_date,
        numinst=dto.numinst,
        request_id=dto.request_id,
        error=dto.error,
        smartlock_status=dto.smartlock_status,
    )


def arm_status_to_dto(value: ArmStatus) -> ArmStatusDTO:
    return ArmStatusDTO(
        "OK" if value.success else "KO",
        value.message,
        value.status,
        value.protom_response,
        value.protom_response_date,
        value.numinst,
        value.request_id,
        value.error,
        value.smartlock_status,
    )


def disarm_status_from_dto(dto: DisarmStatusDTO) -> DisarmStatus:
    return DisarmStatus(
        success=dto.res == "OK",
        message=dto.msg or "",
        status=dto.status,
        protom_response=dto.protom_response,
        protom_response_date=dto.protom_response_date,
        numinst=dto.numinst,
        request_id=dto.request_id,
        error=dto.error,
    )


def disarm_status_to_dto(value: DisarmStatus) -> DisarmStatusDTO:
    return DisarmStatusDTO(
        "OK" if value.success else "KO",
        value.message,
        value.status,
        value.protom_response,
        value.protom_response_date,
        value.numinst,
        value.request_id,
        value.error,
    )


def check_alarm_from_dto(dto: CheckAlarmDTO) -> CheckAlarm:
    return CheckAlarm(dto.res == "OK", dto.msg or "", dto.reference_id)


def check_alarm_to_dto(value: CheckAlarm) -> CheckAlarmDTO:
    return CheckAlarmDTO("OK" if value.success else "KO", value.message, value.reference_id)

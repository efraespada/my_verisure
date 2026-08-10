"""Mappings between device transport DTOs and domain values."""

from ..models.domain.device import Device, DeviceConfig, DeviceConfigFlags, DeviceList
from ..models.dto.device_dto import (
    DeviceConfigDTO,
    DeviceConfigFlagsDTO,
    DeviceDTO,
    DeviceListDTO,
)


def config_flags_from_dto(dto: DeviceConfigFlagsDTO) -> DeviceConfigFlags:
    return DeviceConfigFlags(dto.pin_code, dto.doorbell_button)


def config_flags_to_dto(value: DeviceConfigFlags) -> DeviceConfigFlagsDTO:
    return DeviceConfigFlagsDTO(value.pin_code, value.doorbell_button)


def config_from_dto(dto: DeviceConfigDTO) -> DeviceConfig:
    return DeviceConfig(config_flags_from_dto(dto.flags) if dto.flags else None)


def config_to_dto(value: DeviceConfig) -> DeviceConfigDTO:
    return DeviceConfigDTO(config_flags_to_dto(value.flags) if value.flags else None)


def device_from_dto(dto: DeviceDTO) -> Device:
    return Device(
        id=dto.id,
        code=dto.code,
        name=dto.name,
        type=dto.type,
        subtype=dto.subtype,
        remote_use=dto.remote_use,
        id_service=dto.id_service,
        is_active=dto.is_active,
        serial_number=dto.serial_number,
        config=config_from_dto(dto.config) if dto.config else None,
    )


def device_to_dto(value: Device) -> DeviceDTO:
    return DeviceDTO(
        id=value.id,
        code=value.code,
        name=value.name,
        type=value.type,
        subtype=value.subtype,
        remote_use=value.remote_use,
        id_service=value.id_service,
        is_active=value.is_active,
        serial_number=value.serial_number,
        config=config_to_dto(value.config) if value.config else None,
    )


def device_list_from_dto(dto: DeviceListDTO) -> DeviceList:
    return DeviceList(dto.res, [device_from_dto(device) for device in dto.devices])


def device_list_to_dto(value: DeviceList) -> DeviceListDTO:
    return DeviceListDTO(value.result, [device_to_dto(device) for device in value.devices])

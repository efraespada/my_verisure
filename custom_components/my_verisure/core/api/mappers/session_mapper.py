"""Mappings between session transport DTOs and domain values."""

from ..models.domain.session import DeviceIdentifiers, SessionData
from ..models.dto.session_dto import DeviceIdentifiersDTO, SessionDTO


def device_identifiers_from_dto(dto: DeviceIdentifiersDTO) -> DeviceIdentifiers:
    return DeviceIdentifiers(
        id_device=dto.id_device or "",
        uuid=dto.uuid or "",
        id_device_indigitall=dto.id_device_indigitall or "",
        device_name=dto.device_name or "",
        device_brand=dto.device_brand or "",
        device_os_version=dto.device_os_version or "",
        device_version=dto.device_version or "",
        device_type=dto.device_type or "",
        device_resolution=dto.device_resolution or "",
        generated_time=dto.generated_time or 0,
    )


def device_identifiers_to_dto(value: DeviceIdentifiers) -> DeviceIdentifiersDTO:
    return DeviceIdentifiersDTO(
        id_device=value.id_device,
        uuid=value.uuid,
        id_device_indigitall=value.id_device_indigitall,
        device_name=value.device_name,
        device_brand=value.device_brand,
        device_os_version=value.device_os_version,
        device_version=value.device_version,
        device_type=value.device_type,
        device_resolution=value.device_resolution,
        generated_time=value.generated_time,
    )


def session_data_from_dto(dto: SessionDTO) -> SessionData:
    return SessionData(
        cookies=dto.cookies,
        session_data=dto.session_data or {},
        hash=dto.hash,
        user=dto.user or "",
        device_identifiers=(
            device_identifiers_from_dto(dto.device_identifiers)
            if dto.device_identifiers
            else None
        ),
        saved_time=dto.saved_time or 0,
    )


def session_data_to_dto(value: SessionData) -> SessionDTO:
    return SessionDTO(
        cookies=value.cookies,
        session_data=value.session_data,
        hash=value.hash,
        user=value.user,
        device_identifiers=(
            device_identifiers_to_dto(value.device_identifiers)
            if value.device_identifiers
            else None
        ),
        saved_time=value.saved_time,
    )

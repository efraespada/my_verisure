"""Mappings between session transport DTOs and domain values."""

from ...application.models.session import DeviceIdentifiers, SessionData
from ..models.dto.session_dto import DeviceIdentifiersDTO, SessionDTO


def _required_string(value: str | None, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"session field required: {field}")
    return value


def _required_mapping(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"session field required: {field}")
    return value


def _required_time(value: int | None) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError("session field required: saved_time")
    return value


def device_identifiers_from_dto(dto: DeviceIdentifiersDTO) -> DeviceIdentifiers:
    return DeviceIdentifiers(
        id_device=_required_string(dto.id_device, "id_device"),
        uuid=_required_string(dto.uuid, "uuid"),
        id_device_indigitall=_required_string(dto.id_device_indigitall, "id_device_indigitall"),
        device_name=_required_string(dto.device_name, "device_name"),
        device_brand=_required_string(dto.device_brand, "device_brand"),
        device_os_version=_required_string(dto.device_os_version, "device_os_version"),
        device_version=_required_string(dto.device_version, "device_version"),
        device_type=dto.device_type,
        device_resolution=dto.device_resolution,
        generated_time=dto.generated_time,
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
        cookies=_required_mapping(dto.cookies, "cookies"),
        session_data=_required_mapping(dto.session_data, "session_data"),
        hash=dto.hash,
        user=_required_string(dto.user, "user"),
        device_identifiers=(
            device_identifiers_from_dto(dto.device_identifiers)
            if dto.device_identifiers
            else None
        ),
        saved_time=_required_time(dto.saved_time),
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

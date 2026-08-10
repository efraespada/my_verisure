"""Contract tests for session DTO adapters."""

from custom_components.my_verisure.core.api.mappers.session_mapper import (
    session_data_from_dto,
    session_data_to_dto,
)
from custom_components.my_verisure.core.api.models.domain.session import (
    DeviceIdentifiers,
    SessionData,
)
from custom_components.my_verisure.core.api.models.dto.session_dto import (
    DeviceIdentifiersDTO,
    SessionDTO,
)


def test_session_mapping_round_trip() -> None:
    device = DeviceIdentifiersDTO(
        "id", "uuid", "indigitall", "name", "brand", "os", "version", "", "", 0
    )
    dto = SessionDTO({"cookie": "value"}, {"key": "value"}, "hash", "user", device, 10)
    value = session_data_from_dto(dto)
    assert value == SessionData(
        {"cookie": "value"},
        {"key": "value"},
        "hash",
        "user",
        DeviceIdentifiers("id", "uuid", "indigitall", "name", "brand", "os", "version"),
        10,
    )
    assert session_data_to_dto(value) == dto

"""Contract tests for session DTO adapters."""

from pytest import raises

from custom_components.my_verisure.core.api.mappers.session_mapper import (
    session_data_from_dto,
    session_data_to_dto,
)
from custom_components.my_verisure.core.application.models.session import (
    DeviceIdentifiers,
    SessionData,
)
from custom_components.my_verisure.core.api.models.dto.session_dto import (
    DeviceIdentifiersDTO,
    SessionDTO,
)




def test_session_mapping_rejects_missing_context() -> None:
    with raises(ValueError, match="session field required"):
        session_data_from_dto(SessionDTO({}, None, user=None, saved_time=None))


def test_session_mapping_round_trip() -> None:
    device = DeviceIdentifiersDTO(
        "id", "uuid", "indigitall", "name", "brand", "os", "version", None, None, None
    )
    dto = SessionDTO({"cookie": "value"}, {"key": "value"}, "hash", "user", device, 10)
    value = session_data_from_dto(dto)
    assert value == SessionData(
        cookies={"cookie": "value"},
        session_data={"key": "value"},
        user="user",
        saved_time=10,
        hash="hash",
        device_identifiers=DeviceIdentifiers(
            "id", "uuid", "indigitall", "name", "brand", "os", "version"
        ),
    )
    assert session_data_to_dto(value) == dto

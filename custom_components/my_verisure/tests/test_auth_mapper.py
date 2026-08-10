"""Contract tests for the authentication DTO adapter."""

from custom_components.my_verisure.core.api.mappers.auth_mapper import (
    auth_result_from_dto,
    auth_result_to_dto,
    otp_data_from_dto,
    otp_data_to_dto,
)
from custom_components.my_verisure.core.api.models.dto.auth_dto import (
    AuthDTO,
    OTPDataDTO,
    PhoneDTO,
)
from custom_components.my_verisure.core.api.models.domain.auth import (
    AuthResult,
    OTPData,
    Phone,
)


def test_auth_result_mapping_is_explicit_and_reversible() -> None:
    dto = AuthDTO(res="OK", msg="ok", hash="h", refresh_token="r")
    value = auth_result_from_dto(dto)
    assert value == AuthResult(True, "ok", "h", "r")
    assert auth_result_to_dto(value) == dto


def test_otp_mapping_is_explicit_and_reversible() -> None:
    dto = OTPDataDTO(
        phones=[PhoneDTO(id=1, phone="***")],
        otp_hash="otp",
        auth_code="code",
        auth_type="sms",
    )
    value = otp_data_from_dto(dto)
    assert value == OTPData([Phone(1, "***")], "otp", "code", "sms")
    assert otp_data_to_dto(value) == dto

"""Mappings between authentication transport DTOs and domain values."""

from ..models.domain.auth import AuthResult, OTPData, Phone
from ..models.dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO


def phone_from_dto(dto: PhoneDTO) -> Phone:
    return Phone(id=dto.id, phone=dto.phone)


def phone_to_dto(value: Phone) -> PhoneDTO:
    return PhoneDTO(id=value.id, phone=value.phone)


def otp_data_from_dto(dto: OTPDataDTO) -> OTPData:
    return OTPData(
        phones=[phone_from_dto(phone) for phone in dto.phones],
        otp_hash=dto.otp_hash,
        auth_code=dto.auth_code,
        auth_type=dto.auth_type,
    )


def otp_data_to_dto(value: OTPData) -> OTPDataDTO:
    return OTPDataDTO(
        phones=[phone_to_dto(phone) for phone in value.phones],
        otp_hash=value.otp_hash,
        auth_code=value.auth_code,
        auth_type=value.auth_type,
    )


def auth_result_from_dto(dto: AuthDTO) -> AuthResult:
    return AuthResult(
        success=dto.res == "OK",
        message=dto.msg,
        hash=dto.hash,
        refresh_token=dto.refresh_token,
        lang=dto.lang,
        legals=dto.legals,
        change_password=dto.change_password,
        need_device_authorization=dto.need_device_authorization,
    )


def auth_result_to_dto(value: AuthResult) -> AuthDTO:
    return AuthDTO(
        res="OK" if value.success else "KO",
        msg=value.message,
        hash=value.hash,
        refresh_token=value.refresh_token,
        lang=value.lang,
        legals=value.legals,
        change_password=value.change_password,
        need_device_authorization=value.need_device_authorization,
    )

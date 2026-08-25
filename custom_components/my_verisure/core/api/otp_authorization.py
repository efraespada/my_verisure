"""Pure OTP preparation and phone-selection rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..application.otp_code_policy import is_valid_otp_code
from ..application.models.auth import Phone


@dataclass(frozen=True)
class PreparedOTPData:
    """Validated OTP data safe for the client state boundary."""

    phones: tuple[Phone, ...]
    otp_hash: str


class OTPAuthorizationPolicy:
    """Validate OTP metadata and select a destination phone."""

    def prepare(self, data: Mapping[str, Any]) -> PreparedOTPData | None:
        raw_phones = data.get("auth-phones")
        otp_hash = data.get("auth-otp-hash")
        if (
            not isinstance(raw_phones, list)
            or not raw_phones
            or not isinstance(otp_hash, str)
            or not otp_hash.strip()
        ):
            return None

        phones: list[Phone] = []
        for phone in raw_phones:
            if not isinstance(phone, Mapping):
                return None
            phone_id = phone.get("id")
            phone_number = phone.get("phone")
            if (
                isinstance(phone_id, bool)
                or not isinstance(phone_id, int)
                or phone_id <= 0
                or not isinstance(phone_number, str)
                or not phone_number
            ):
                return None
            record_id_from_camel = phone.get("recordId")
            record_id_from_snake = phone.get("record_id")
            if (
                record_id_from_camel is not None
                and record_id_from_snake is not None
                and record_id_from_camel != record_id_from_snake
            ):
                return None
            record_id = (
                record_id_from_camel
                if record_id_from_camel is not None
                else record_id_from_snake
            )
            if (
                isinstance(record_id, bool)
                or not isinstance(record_id, int)
                or record_id <= 0
            ):
                return None
            phones.append(
                Phone(
                    id=phone_id,
                    phone=phone_number,
                    record_id=record_id,
                )
            )

        if not phones:
            return None
        return PreparedOTPData(phones=tuple(phones), otp_hash=otp_hash)

    def select_phone(
        self, phones: tuple[Phone, ...], phone_id: int
    ) -> Phone | None:
        if isinstance(phone_id, bool) or not isinstance(phone_id, int) or phone_id <= 0:
            return None
        return next((phone for phone in phones if phone.id == phone_id), None)

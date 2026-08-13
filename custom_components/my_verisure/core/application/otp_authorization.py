"""Pure OTP preparation and phone-selection rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ..api.models.dto.auth_dto import PhoneDTO


@dataclass(frozen=True)
class PreparedOTPData:
    """Validated OTP data safe for the client state boundary."""

    phones: tuple[PhoneDTO, ...]
    otp_hash: str


class OTPAuthorizationPolicy:
    """Validate OTP metadata and select a destination phone."""

    def prepare(self, data: Mapping[str, Any]) -> PreparedOTPData | None:
        raw_phones = data.get("auth-phones")
        otp_hash = data.get("auth-otp-hash")
        if not isinstance(raw_phones, list) or not raw_phones or not otp_hash:
            return None

        phones = tuple(
            PhoneDTO(
                id=int(phone.get("id", 0)),
                phone=str(phone.get("phone", "")),
                record_id=phone.get("id"),
                otp_hash=str(otp_hash),
            )
            for phone in raw_phones
            if isinstance(phone, Mapping)
        )
        if not phones:
            return None
        return PreparedOTPData(phones=phones, otp_hash=str(otp_hash))

    def select_phone(
        self, phones: tuple[PhoneDTO, ...], phone_id: int
    ) -> PhoneDTO | None:
        return next((phone for phone in phones if phone.id == phone_id), None)

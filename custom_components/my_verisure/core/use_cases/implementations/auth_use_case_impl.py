"""Authentication use case implementation."""

import logging
from typing import List

from ...api.models.domain.auth import Auth, AuthResult
from ...repositories.interfaces.auth_repository import AuthRepository
from ..interfaces.auth_use_case import AuthUseCase
from ...api.exceptions import MyVerisureOTPError
from ...log_utils import redact_otp_message, redact_sensitive_data, should_log_detailed

_LOGGER = logging.getLogger(__name__)


class AuthUseCaseImpl(AuthUseCase):
    """Implementation of authentication use case."""

    def __init__(self, auth_repository: AuthRepository):
        """Initialize the use case with dependencies."""
        self.auth_repository = auth_repository
        self._otp_data = None

    async def login(self, username: str, password: str) -> AuthResult:
        """Login with username and password."""
        try:
            _LOGGER.info("Starting login process for user: %s", username)

            result = await self.auth_repository.login(
                Auth(username=username, password=password)
            )

            if not result.success:
                _LOGGER.warning("Login failed for user: %s", username)

            return result

        except MyVerisureOTPError as e:
            _LOGGER.info("OTP authentication required: %s", e)
            # Store OTP data from the auth client for later use
            self._otp_data = getattr(e, "otp_data", e)
            if should_log_detailed():
                _LOGGER.debug(
                    "Stored OTP data in AuthUseCase (redacted): %s",
                    redact_sensitive_data(self._otp_data),
                )
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during login: %s", e)
            raise

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        try:
            _LOGGER.info("Sending OTP for record_id: %s", record_id)

            result = await self.auth_repository.send_otp(record_id, otp_hash)

            if result:
                _LOGGER.info("OTP sent successfully")
            else:
                _LOGGER.error("Failed to send OTP")

            return result

        except Exception as e:
            _LOGGER.error("Error sending OTP: %s", e)
            raise

    async def verify_otp(self, otp_code: str) -> bool:
        """Verify OTP code."""
        try:
            _LOGGER.info("Verifying OTP: %s", redact_otp_message())

            result = await self.auth_repository.verify_otp(otp_code)

            if result:
                _LOGGER.info("OTP verification successful")
            else:
                _LOGGER.error("OTP verification failed")

            return result

        except Exception as e:
            _LOGGER.error("Error verifying OTP: %s", e)
            raise

    def get_available_phones(self) -> List[dict]:
        """Get available phone numbers for OTP."""
        _LOGGER.debug("Getting available phones from auth use case")
        if should_log_detailed():
            _LOGGER.debug(
                "AuthUseCase _otp_data (redacted): %s",
                redact_sensitive_data(self._otp_data),
            )

        phones = getattr(self._otp_data, "phones", None)
        if phones:
            return [
                {
                    key: value
                    for key, value in {
                        "id": phone.id,
                        "phone": phone.phone,
                        "record_id": getattr(phone, "record_id", None),
                        "otp_hash": getattr(phone, "otp_hash", None),
                    }.items()
                    if value is not None
                }
                for phone in phones
            ]

        if not self._otp_data:
            _LOGGER.debug("No OTP data available in AuthUseCase")
            return []

        # Check if _otp_data is a dictionary with phones
        if isinstance(self._otp_data, dict) and "phones" in self._otp_data:
            phones = self._otp_data.get("phones", [])
            result = [
                {
                    "id": phone.get("id"),
                    "phone": phone.get("phone"),
                    "record_id": phone.get("record_id"),
                    "otp_hash": phone.get("otp_hash"),
                }
                for phone in phones
            ]
            _LOGGER.debug("Returning %d phones from stored data", len(result))
            return result
        # Fallback to client
        _LOGGER.debug("_otp_data is not a dict, delegating to client")
        phones = self.auth_repository.client.get_available_phones()
        result = [
            {
                "id": phone.id,
                "phone": phone.phone,
                "record_id": phone.record_id,
                "otp_hash": phone.otp_hash,
            }
            for phone in phones
        ]
        _LOGGER.debug("Returning %d phones to config flow", len(result))
        return result

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.debug("Selecting phone ID: %d", phone_id)

        if not self._otp_data:
            _LOGGER.error("No OTP data available")
            return False

        # Check if _otp_data is a dictionary with phones
        if isinstance(self._otp_data, dict) and "phones" in self._otp_data:
            phones = self._otp_data["phones"]
            if should_log_detailed():
                _LOGGER.debug(
                    "Available phones from stored data (redacted): %s",
                    redact_sensitive_data(
                        [{"id": p.get("id"), "phone": p.get("phone")} for p in phones]
                    ),
                )
            selected_phone = next((p for p in phones if p.get("id") == phone_id), None)
        else:
            _LOGGER.error("OTP data is not a dictionary with phones: %s", type(self._otp_data))
            return False

        if selected_phone:
            _LOGGER.info("Phone selected for OTP (id=%s)", phone_id)
            return True
        else:
            _LOGGER.error(
                "Phone ID %d not found in available phones", phone_id
            )
            return False

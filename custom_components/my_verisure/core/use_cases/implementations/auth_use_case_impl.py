"""Authentication use case implementation."""

import logging
from typing import List

from ...api.models.domain.auth import Auth, AuthResult
from ...api.models.domain.session import DeviceIdentifiers
from ...repositories.interfaces.auth_repository import AuthRepository
from ..interfaces.auth_use_case import AuthUseCase
from ...api.exceptions import MyVerisureOTPError

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
            _LOGGER.warning("OTP authentication required: %s", e)
            # Store OTP data from the auth client for later use
            self._otp_data = self.auth_repository.client._otp_data
            _LOGGER.warning("Stored OTP data in AuthUseCase: %s", self._otp_data)
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
            _LOGGER.info("Verifying OTP code: %s", otp_code)

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
        _LOGGER.warning("Getting available phones from auth use case")
        _LOGGER.warning("AuthUseCase _otp_data: %s", self._otp_data)
        
        if not self._otp_data:
            _LOGGER.warning("No OTP data available in AuthUseCase")
            return []
        
        # Check if _otp_data is a dictionary with phones
        if isinstance(self._otp_data, dict) and "phones" in self._otp_data:
            _LOGGER.warning("Using stored OTP data from AuthUseCase")
            phones = self._otp_data.get("phones", [])
            result = [{"id": phone.get("id"), "phone": phone.get("phone"), "record_id": phone.get("record_id"), "otp_hash": phone.get("otp_hash")} for phone in phones]
            _LOGGER.warning("Returning %d phones from stored data", len(result))
            return result
        else:
            # Fallback to client
            _LOGGER.warning("_otp_data is not a dict, delegating to client")
            phones = self.auth_repository.client.get_available_phones()
            _LOGGER.warning("Auth client returned %d phones", len(phones))
            result = [{"id": phone.id, "phone": phone.phone, "record_id": phone.record_id, "otp_hash": phone.otp_hash} for phone in phones]
            _LOGGER.warning("Returning %d phones to config flow", len(result))
            return result

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.warning("Selecting phone ID: %d", phone_id)
        _LOGGER.warning("OTP data available: %s", bool(self._otp_data))

        if not self._otp_data:
            _LOGGER.error("No OTP data available")
            return False

        # Check if _otp_data is a dictionary with phones
        if isinstance(self._otp_data, dict) and "phones" in self._otp_data:
            phones = self._otp_data["phones"]
            _LOGGER.warning("Available phones from stored data: %s", [{"id": p.get("id"), "phone": p.get("phone")} for p in phones])
            selected_phone = next((p for p in phones if p.get("id") == phone_id), None)
        else:
            _LOGGER.error("OTP data is not a dictionary with phones: %s", type(self._otp_data))
            return False

        if selected_phone:
            _LOGGER.warning(
                "Phone selected: ID %d - %s", phone_id, selected_phone.get("phone")
            )
            return True
        else:
            _LOGGER.error(
                "Phone ID %d not found in available phones", phone_id
            )
            return False

"""Authentication use case implementation."""

import logging
from typing import List

from api.models.domain.auth import Auth, AuthResult
from api.models.domain.session import DeviceIdentifiers
from repositories.interfaces.auth_repository import AuthRepository
from use_cases.interfaces.auth_use_case import AuthUseCase
from api.exceptions import MyVerisureOTPError

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

            # Create domain models
            auth = Auth(username=username, password=password)

            # Generate device identifiers (change this)
            device_identifiers = DeviceIdentifiers(
                id_device="device_123",
                uuid="uuid_456",
                id_device_indigitall="indigitall_789",
                device_name="HomeAssistant",
                device_brand="HomeAssistant",
                device_os_version="Linux 5.0",
                device_version="10.154.0",
            )

            # Call repository
            result = await self.auth_repository.login(auth, device_identifiers)

            if result.success:
                _LOGGER.info("Login successful for user: %s", username)
            else:
                _LOGGER.warning("Login failed for user: %s", username)

            return result

        except MyVerisureOTPError as e:
            _LOGGER.info("OTP authentication required: %s", e)
            # Store OTP data for later use
            self._otp_data = e
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
            _LOGGER.info("Verifying OTP code")

            if not self._otp_data:
                raise ValueError("No OTP data available. Please login first.")

            # Get OTP hash from stored data
            otp_hash = getattr(self._otp_data, "otp_hash", None)
            if not otp_hash:
                raise ValueError("No OTP hash available")

            # Create device identifiers (same as in login)
            device_identifiers = DeviceIdentifiers(
                id_device="device_123",
                uuid="uuid_456",
                id_device_indigitall="indigitall_789",
                device_name="HomeAssistant",
                device_brand="HomeAssistant",
                device_os_version="Linux 5.0",
                device_version="10.154.0",
            )

            result = await self.auth_repository.verify_otp(
                otp_code, otp_hash, device_identifiers
            )

            if result.success:
                _LOGGER.info("OTP verification successful")
                # Clear OTP data after successful verification
                self._otp_data = None
            else:
                _LOGGER.error("OTP verification failed")

            return result.success

        except Exception as e:
            _LOGGER.error("Error verifying OTP: %s", e)
            raise

    def get_available_phones(self) -> List[dict]:
        """Get available phone numbers for OTP."""
        if not self._otp_data:
            return []

        # Extract phone data from OTP exception
        phones = getattr(self._otp_data, "phones", [])
        return [{"id": phone.id, "phone": phone.phone} for phone in phones]

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.debug("Selecting phone ID: %d", phone_id)

        if not self._otp_data:
            _LOGGER.error("No OTP data available")
            return False

        phones = getattr(self._otp_data, "phones", [])
        selected_phone = next((p for p in phones if p.id == phone_id), None)

        if selected_phone:
            _LOGGER.info(
                "Phone selected: ID %d - %s", phone_id, selected_phone.phone
            )
            return True
        else:
            _LOGGER.error(
                "Phone ID %d not found in available phones", phone_id
            )
            return False

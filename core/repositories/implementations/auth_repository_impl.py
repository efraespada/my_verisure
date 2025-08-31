"""Authentication repository implementation."""

import logging
from typing import List, Dict, Any

from api.models.domain.auth import Auth, AuthResult
from api.models.domain.session import DeviceIdentifiers
from api.models.dto.auth_dto import AuthDTO
from repositories.interfaces.auth_repository import AuthRepository
from api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
)

_LOGGER = logging.getLogger(__name__)


class AuthRepositoryImpl(AuthRepository):
    """Implementation of authentication repository."""

    def __init__(self, client):
        """Initialize the repository with a client."""
        self.client = client

    async def login(
        self, auth: Auth, device_identifiers: DeviceIdentifiers
    ) -> AuthResult:
        """Login with username and password."""
        try:
            _LOGGER.info("Attempting login for user: %s", auth.username)

            # Ensure client is connected
            if not self.client._client:
                _LOGGER.info("Client not connected, connecting now...")
                await self.client.connect()

            # Convert domain models to DTOs for the client
            # Note: DTOs are created but not used in this implementation
            # as the client handles the conversion internally
            _ = AuthDTO(
                res="",  # Will be filled by client
                msg="",
                hash=None,
                refresh_token=None,
            )

            _ = device_identifiers.to_dto()

            # Call the client's login method
            result = await self.client.login()

            # Debug: Check client state after login
            _LOGGER.info("Login result: %s", result)
            _LOGGER.info(
                "Client hash token after login: %s",
                "Yes" if self.client._hash else "No",
            )
            _LOGGER.info(
                "Client session data after login: %s",
                self.client._session_data,
            )

            # The client.login() returns a boolean, but the token is stored internally
            # Check if the client has the hash token after login
            if result and self.client._hash:
                _LOGGER.info(
                    "Login successful with token: %s",
                    (
                        self.client._hash[:50] + "..."
                        if self.client._hash
                        else "None"
                    ),
                )
                return AuthResult(
                    success=True,
                    message="Login successful",
                    hash=self.client._hash,
                    refresh_token=self.client._refresh_token,
                    lang=self.client._session_data.get("lang"),
                    legals=self.client._session_data.get("legals"),
                    change_password=self.client._session_data.get(
                        "changePassword"
                    ),
                    need_device_authorization=self.client._session_data.get(
                        "needDeviceAuthorization"
                    ),
                )
            else:
                _LOGGER.error(
                    "Login failed - result: %s, hash present: %s",
                    result,
                    "Yes" if self.client._hash else "No",
                )
                return AuthResult(success=False, message="Login failed")

        except MyVerisureOTPError as e:
            _LOGGER.info("OTP authentication required: %s", e)
            return AuthResult(
                success=False,
                message=f"OTP authentication required: {e}",
                hash=None,
                refresh_token=None,
            )
        except MyVerisureAuthenticationError as e:
            _LOGGER.error("Authentication failed: %s", e)
            return AuthResult(
                success=False,
                message=f"Authentication failed: {e}",
                hash=None,
                refresh_token=None,
            )
        except Exception as e:
            _LOGGER.error("Unexpected error during login: %s", e)
            return AuthResult(
                success=False,
                message=f"Login failed: {e}",
                hash=None,
                refresh_token=None,
            )

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        try:
            _LOGGER.info("Sending OTP for record_id: %s", record_id)

            result = await self.client.send_otp(record_id, otp_hash)

            if result:
                _LOGGER.info("OTP sent successfully")
                return True
            else:
                _LOGGER.error("Failed to send OTP")
                return False

        except Exception as e:
            _LOGGER.error("Error sending OTP: %s", e)
            raise MyVerisureOTPError(f"Failed to send OTP: {e}") from e

    async def verify_otp(
        self,
        otp_code: str,
        otp_hash: str,
        device_identifiers: DeviceIdentifiers,
    ) -> AuthResult:
        """Verify OTP code."""
        try:
            _LOGGER.info("Verifying OTP code")

            result = await self.client.verify_otp(otp_code)

            if result:
                return AuthResult(
                    success=True,
                    message="OTP verification successful",
                    hash=self.client._hash,
                    refresh_token=self.client._refresh_token,
                    lang=self.client._session_data.get("lang"),
                    legals=self.client._session_data.get("legals"),
                    change_password=self.client._session_data.get(
                        "changePassword"
                    ),
                    need_device_authorization=self.client._session_data.get(
                        "needDeviceAuthorization"
                    ),
                )
            else:
                return AuthResult(
                    success=False, message="OTP verification failed"
                )

        except MyVerisureOTPError as e:
            _LOGGER.error("OTP verification failed: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during OTP verification: %s", e)
            raise MyVerisureOTPError(f"OTP verification failed: {e}") from e

    async def validate_device(
        self, device_identifiers: DeviceIdentifiers
    ) -> AuthResult:
        """Validate device with the API."""
        try:
            _LOGGER.info("Validating device")

            # This would typically call the client's device validation method
            # For now, we'll assume the device is already validated if we have a hash
            if self.client._hash:
                return AuthResult(
                    success=True,
                    message="Device validation successful",
                    hash=self.client._hash,
                    refresh_token=self.client._refresh_token,
                )
            else:
                return AuthResult(
                    success=False,
                    message="Device validation failed - no hash available",
                )

        except Exception as e:
            _LOGGER.error("Error validating device: %s", e)
            raise MyVerisureDeviceAuthorizationError(
                f"Device validation failed: {e}"
            ) from e

    def get_available_phones(self) -> List[Dict[str, Any]]:
        """Get available phone numbers for OTP."""
        try:
            _LOGGER.info("Getting available phones for OTP")

            # Call the client's get_available_phones method
            phones = self.client.get_available_phones()

            if phones:
                _LOGGER.info("Found %d available phones", len(phones))
                return phones
            else:
                _LOGGER.warning("No available phones found")
                return []

        except Exception as e:
            _LOGGER.error("Error getting available phones: %s", e)
            return []

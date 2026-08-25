"""Authentication repository implementation."""

import asyncio
import logging

import aiohttp

from ...application.models.auth import Auth, AuthResult
from ...api.models.dto.auth_dto import AuthDTO
from ..interfaces.auth_repository import AuthRepository
from ...api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureOTPError,
    MyVerisureTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


class AuthRepositoryImpl(AuthRepository):
    """Implementation of authentication repository."""

    def __init__(self, client):
        """Initialize the repository with a client."""
        self.client = client

    async def login(
        self, auth: Auth
    ) -> AuthResult:
        """Login with username and password."""
        try:
            _LOGGER.info("Login started")

            result = await self.client.login(auth.username, auth.password)

            _LOGGER.info(
                "Login result: success=%s",
                getattr(result, "success", False),
            )

            if (
                isinstance(result, AuthDTO)
                and result.res == "OK"
                and result.need_device_authorization is False
                and isinstance(result.hash, str)
                and bool(result.hash.strip())
            ):
                return AuthResult(
                    success=True,
                    message="Login successful",
                    hash=result.hash,
                    refresh_token=result.refresh_token,
                    lang=result.lang,
                    legals=result.legals,
                    change_password=result.change_password,
                    need_device_authorization=result.need_device_authorization,
                )

            _LOGGER.error("Login failed — provider returned no valid session")
            return AuthResult(success=False, message="Login failed")

        except MyVerisureConnectionError:
            raise
        except aiohttp.ClientError:
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except TimeoutError:
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except asyncio.CancelledError:
            raise
        except OSError:
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except MyVerisureOTPError:
            _LOGGER.info("OTP authentication required")
            raise
        except MyVerisureAuthenticationError:
            _LOGGER.error("Authentication failed")
            return AuthResult(
                success=False,
                message="invalid credentials",
                hash=None,
                refresh_token=None,
            )
        except Exception:
            _LOGGER.error("Login transport failed")
            raise MyVerisureConnectionError("Authentication transport failed") from None

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        try:
            _LOGGER.info("OTP send started")

            result = await self.client.send_otp(record_id, otp_hash)

            if result:
                _LOGGER.info("OTP sent successfully")
                return True
            else:
                _LOGGER.error("Failed to send OTP")
                return False

        except MyVerisureConnectionError:
            raise
        except aiohttp.ClientError:
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except TimeoutError:
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except asyncio.CancelledError:
            raise
        except OSError:
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except MyVerisureOTPError:
            raise
        except MyVerisureAuthenticationError:
            raise
        except Exception:
            _LOGGER.error("OTP send transport failed")
            raise MyVerisureConnectionError("Authentication transport failed") from None

    async def verify_otp(self, otp_code: str) -> AuthResult:
        """Verify OTP code."""
        try:
            _LOGGER.info("Verifying OTP code")

            result = await self.client.verify_otp(otp_code)

            if (
                isinstance(result, AuthDTO)
                and result.res == "OK"
                and result.need_device_authorization is False
                and isinstance(result.hash, str)
                and bool(result.hash.strip())
            ):
                return AuthResult(
                    success=True,
                    message="OTP verification successful",
                    hash=result.hash,
                    refresh_token=result.refresh_token,
                    lang=result.lang,
                    legals=result.legals,
                    change_password=result.change_password,
                    need_device_authorization=result.need_device_authorization,
                )

            return AuthResult(
                success=False,
                message="OTP verification failed",
            )

        except MyVerisureConnectionError:
            raise
        except aiohttp.ClientError:
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except TimeoutError:
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except asyncio.CancelledError:
            raise
        except OSError:
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except MyVerisureOTPError:
            raise
        except MyVerisureDeviceAuthorizationError:
            raise
        except MyVerisureAuthenticationError:
            raise
        except Exception:
            _LOGGER.error("OTP verification transport failed")
            raise MyVerisureConnectionError("Authentication transport failed") from None

    def invalidate_otp_challenge(self) -> None:
        """Invalidate provider-client OTP state without network access."""
        self.client.invalidate_otp_challenge()

    def get_available_phones(self) -> list[dict[str, object]]:
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

        except MyVerisureConnectionError:
            raise
        except Exception:
            _LOGGER.error("OTP phone lookup failed")
            raise MyVerisureConnectionError("OTP phone lookup failed") from None

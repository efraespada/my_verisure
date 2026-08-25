"""Authentication use case implementation."""

import asyncio
import logging
import time
from typing import List

from ...application.models.auth import Auth, AuthResult, OTPData, Phone
from ...application.auth_session_persistence import AuthSessionPersistence
from ...application.otp_code_policy import is_valid_otp_code
from ...repositories.interfaces.auth_repository import AuthRepository
from ..interfaces.auth_use_case import AuthUseCase
from ...application.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureOTPError,
    MyVerisurePersistenceError,
    MyVerisureTimeoutError,
)
from ...log_utils import redact_sensitive_data, should_log_detailed

_LOGGER = logging.getLogger(__name__)

OTP_CHALLENGE_TTL_SECONDS = 300
MAX_OTP_ATTEMPTS = 3


class AuthUseCaseImpl(AuthUseCase):
    """Implementation of authentication use case."""

    def __init__(
        self,
        auth_repository: AuthRepository,
        session_persistence: AuthSessionPersistence,
    ):
        """Initialize the use case with explicit authentication boundaries."""
        self.auth_repository = auth_repository
        self._session_persistence = session_persistence
        self._otp_data: OTPData | None = None
        self._otp_expires_at: float | None = None
        self._otp_attempts = 0
        self._selected_phone: Phone | None = None
        self._pending_credentials: tuple[str, str] | None = None

    def invalidate_otp_challenge(self) -> None:
        """Invalidate application and provider-client OTP state together."""
        self._otp_data = None
        self._otp_expires_at = None
        self._otp_attempts = 0
        self._selected_phone = None
        self._pending_credentials = None
        self.auth_repository.invalidate_otp_challenge()

    async def login(self, username: str, password: str) -> AuthResult:
        """Login with username and password."""
        self.invalidate_otp_challenge()
        self._pending_credentials = (username, password)
        try:
            _LOGGER.info("Login started")

            result = await self.auth_repository.login(
                Auth(username=username, password=password)
            )

            if result.success:
                credentials = self._pending_credentials
                if credentials is None:
                    raise MyVerisurePersistenceError("Authentication credentials unavailable")
                username, password = credentials
                await self._session_persistence.persist_result(
                    result,
                    username=username,
                    password=password,
                )
                self._pending_credentials = None
            else:
                self.invalidate_otp_challenge()
                _LOGGER.warning("Login failed")

            return result

        except MyVerisureOTPError as error:
            challenge_phones = tuple(error.phones)
            challenge_hash = error.otp_hash
            valid_phone_binding = all(
                not isinstance(phone.id, bool)
                and isinstance(phone.id, int)
                and phone.id > 0
                and isinstance(phone.phone, str)
                and bool(phone.phone)
                and not isinstance(phone.record_id, bool)
                and isinstance(phone.record_id, int)
                and phone.record_id > 0
                for phone in challenge_phones
            )
            if (
                not challenge_phones
                or not valid_phone_binding
                or not isinstance(challenge_hash, str)
                or not challenge_hash.strip()
            ):
                self.invalidate_otp_challenge()
                raise MyVerisureAuthenticationError(
                    "Authentication challenge unavailable"
                ) from None
            _LOGGER.info("OTP authentication required")
            self._otp_data = OTPData(
                phones=[
                    Phone(
                        id=int(phone.id),
                        phone=str(phone.phone),
                        record_id=phone.record_id,
                    )
                    for phone in challenge_phones
                ],
                otp_hash=challenge_hash,
            )
            self._otp_expires_at = time.monotonic() + OTP_CHALLENGE_TTL_SECONDS
            self._otp_attempts = 0
            self._selected_phone = None
            if should_log_detailed():
                _LOGGER.debug(
                    "Stored OTP data in AuthUseCase (redacted): %s",
                    redact_sensitive_data(self._otp_data),
                )
            raise
        except asyncio.CancelledError:
            self.invalidate_otp_challenge()
            raise
        except Exception:
            self.invalidate_otp_challenge()
            _LOGGER.error("Login failed")
            raise

    async def send_otp(self, record_id: int, otp_hash: str | None = None) -> bool:
        """Send OTP only to the selected, validated challenge destination."""
        try:
            if (
                isinstance(record_id, bool)
                or not isinstance(record_id, int)
                or record_id <= 0
            ):
                raise MyVerisureOTPError("Invalid OTP record")
            if self._otp_attempts >= MAX_OTP_ATTEMPTS:
                self.invalidate_otp_challenge()
                raise MyVerisureOTPError("OTP maximum attempts exceeded")
            if self._otp_data is None or not self._otp_data.otp_hash:
                raise MyVerisureOTPError("OTP challenge unavailable")
            if self._selected_phone is None:
                raise MyVerisureOTPError("OTP phone must be selected")
            selected_record_id = self._selected_phone.record_id
            if selected_record_id != record_id:
                raise MyVerisureOTPError("OTP record does not match selected phone")
            if self._otp_expires_at is None or time.monotonic() >= self._otp_expires_at:
                raise MyVerisureOTPError("OTP challenge expired")
            if otp_hash is None:
                otp_hash = self._otp_data.otp_hash
            if otp_hash != self._otp_data.otp_hash:
                raise MyVerisureOTPError("OTP challenge hash mismatch")

            _LOGGER.info("OTP send started")
            result = await self.auth_repository.send_otp(record_id, otp_hash)

            if result:
                _LOGGER.info("OTP sent successfully")
            else:
                self.invalidate_otp_challenge()
                _LOGGER.error("Failed to send OTP")

            return result

        except asyncio.CancelledError:
            self.invalidate_otp_challenge()
            raise
        except Exception:
            self.invalidate_otp_challenge()
            _LOGGER.error("OTP send failed")
            raise

    async def verify_otp(self, otp_code: str) -> AuthResult:
        """Verify OTP code."""
        retryable_provider_rejection = False
        try:
            if self._otp_data is None:
                raise MyVerisureOTPError("No active OTP challenge")
            if self._otp_expires_at is None or time.monotonic() >= self._otp_expires_at:
                raise MyVerisureOTPError("OTP challenge expired")
            if self._otp_attempts >= MAX_OTP_ATTEMPTS:
                self.invalidate_otp_challenge()
                raise MyVerisureOTPError("OTP maximum attempts exceeded")
            if not is_valid_otp_code(otp_code):
                self.invalidate_otp_challenge()
                raise MyVerisureOTPError("OTP code format invalid")

            _LOGGER.info("OTP verification started")
            try:
                result = await self.auth_repository.verify_otp(otp_code)
            except MyVerisureOTPError as error:
                if not error.retryable:
                    self.invalidate_otp_challenge()
                    raise
                retryable_provider_rejection = True
                self._otp_attempts += 1
                if self._otp_attempts >= MAX_OTP_ATTEMPTS:
                    self.invalidate_otp_challenge()
                raise
            except (
                asyncio.CancelledError,
                MyVerisureConnectionError,
                MyVerisureAuthenticationError,
                MyVerisureDeviceAuthorizationError,
                OSError,
                TimeoutError,
            ):
                raise

            if result.success:
                # Provider acceptance irreversibly consumes the challenge before
                # persistence, which may fail or be cancelled.
                credentials = self._pending_credentials
                self.invalidate_otp_challenge()
                try:
                    if credentials is None:
                        await self._session_persistence.persist_result(result)
                    else:
                        await self._session_persistence.persist_result(
                            result,
                            username=credentials[0],
                            password=credentials[1],
                        )
                except asyncio.CancelledError:
                    raise
                except MyVerisurePersistenceError:
                    raise
                except Exception:
                    raise MyVerisureAuthenticationError(
                        "OTP verification did not establish an authenticated session"
                    ) from None

                _LOGGER.info("OTP verification successful and session persisted")
            else:
                self.invalidate_otp_challenge()
                _LOGGER.error("OTP verification failed")

            return result

        except asyncio.CancelledError:
            self.invalidate_otp_challenge()
            raise
        except MyVerisureOTPError:
            if not retryable_provider_rejection:
                self.invalidate_otp_challenge()
            raise
        except (
            MyVerisureConnectionError,
            MyVerisureAuthenticationError,
            MyVerisureDeviceAuthorizationError,
            MyVerisurePersistenceError,
            MyVerisureTimeoutError,
            OSError,
            TimeoutError,
        ):
            self.invalidate_otp_challenge()
            raise
        except Exception:
            self.invalidate_otp_challenge()
            _LOGGER.error("OTP verification failed")
            raise MyVerisureOTPError("OTP verification failed") from None

    def get_available_phones(self) -> List[dict]:
        """Get available phone numbers for OTP."""
        _LOGGER.debug("Getting available phones from auth use case")
        if should_log_detailed():
            _LOGGER.debug(
                "AuthUseCase _otp_data (redacted): %s",
                redact_sensitive_data(self._otp_data),
            )

        if self._otp_data is None:
            _LOGGER.error("OTP challenge unavailable")
            self.invalidate_otp_challenge()
            raise MyVerisureConnectionError("OTP challenge unavailable")

        try:
            return [
                {
                    "id": phone.id,
                    "phone": phone.phone,
                    "record_id": phone.record_id,
                }
                for phone in self._otp_data.phones
            ]
        except Exception:
            self.invalidate_otp_challenge()
            raise MyVerisureConnectionError("OTP challenge unavailable") from None

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.debug("Selecting OTP phone")

        if self._otp_data is None:
            _LOGGER.error("No OTP data available")
            return False

        if (
            isinstance(phone_id, bool)
            or not isinstance(phone_id, int)
            or phone_id <= 0
        ):
            _LOGGER.error("Selected OTP phone is not available")
            return False

        selected_phone = next(
            (phone for phone in self._otp_data.phones if phone.id == phone_id),
            None,
        )
        if selected_phone is None or not isinstance(selected_phone.record_id, int):
            _LOGGER.error("Selected OTP phone is not available")
            return False

        self._selected_phone = selected_phone
        _LOGGER.info("OTP phone selected")
        return True

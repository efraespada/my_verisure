"""Authentication client for My Verisure API."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import aiohttp

from .base_client import BaseClient
from .auth_response_classifier import LoginResponse, classify_login_response
from .auth_session_projection import build_session_data
from .device_authorization_response import (
    DeviceAuthorizationFailure,
    DeviceAuthorizationOTPChallenge,
    DeviceAuthorizationSuccess,
    classify_device_authorization_response,
)
from ..application.exceptions import MyVerisurePersistenceError
from .otp_authorization import OTPAuthorizationPolicy
from ..application.otp_code_policy import is_valid_otp_code
from .otp_verification_response import (
    OTPVerificationFailure,
    classify_otp_verification_response,
)
from ..application.models.auth import Phone
from .device_manager import DeviceManager
from .exceptions import (
    MyVerisureError,
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureTimeoutError,
)
from .models.dto.auth_dto import AuthDTO, PhoneDTO
from ..session_manager import SessionManager
from ..log_utils import redact_sensitive_data, should_log_detailed

_LOGGER = logging.getLogger(__name__)

# GraphQL mutations
LOGIN_MUTATION = """
mutation mkLoginToken($user: String!, $password: String!, $id: String!, $country: String!, $idDevice: String, $idDeviceIndigitall: String, $deviceType: String, $deviceVersion: String, $deviceResolution: String, $lang: String!, $callby: String!, $uuid: String, $deviceName: String, $deviceBrand: String, $deviceOsVersion: String, $deviceUseBiometric: String, $phoneAsLogin: Boolean) {
    xSLoginToken(
        user: $user
        password: $password
        id: $id
        country: $country
        idDevice: $idDevice
        idDeviceIndigitall: $idDeviceIndigitall
        deviceType: $deviceType
        deviceVersion: $deviceVersion
        deviceResolution: $deviceResolution
        lang: $lang
        callby: $callby
        uuid: $uuid
        deviceName: $deviceName
        deviceBrand: $deviceBrand
        deviceOsVersion: $deviceOsVersion
        deviceUseBiometric: $deviceUseBiometric
        phoneAsLogin: $phoneAsLogin
    ) {
        res
        msg
        hash
        lang
        legals
        changePassword
        needDeviceAuthorization
        refreshToken
    }
}
"""

REFRESH_LOGIN_MUTATION = """
mutation RefreshLogin($refreshToken: String!, $id: String!, $country: String!, $lang: String!, $callby: String!, $idDevice: String, $idDeviceIndigitall: String, $deviceType: String, $deviceName: String, $deviceBrand: String, $deviceVersion: String, $deviceOsVersion: String, $deviceResolution: String, $uuid: String) {
    xSRefreshLogin(refreshToken: $refreshToken, id: $id, country: $country, lang: $lang, callby: $callby, idDevice: $idDevice, idDeviceIndigitall: $idDeviceIndigitall, deviceType: $deviceType, deviceName: $deviceName, deviceBrand: $deviceBrand, deviceVersion: $deviceVersion, deviceOsVersion: $deviceOsVersion, deviceResolution: $deviceResolution, uuid: $uuid) {
        res msg lang hash refreshToken legals changePassword needDeviceAuthorization
    }
}
"""

VALIDATE_DEVICE_MUTATION = """
mutation mkValidateDevice($idDevice: String, $idDeviceIndigitall: String, $uuid: String, $deviceName: String, $deviceBrand: String, $deviceOsVersion: String, $deviceVersion: String, $password: String) {
    xSValidateDevice(
        idDevice: $idDevice
        idDeviceIndigitall: $idDeviceIndigitall
        uuid: $uuid
        deviceName: $deviceName
        deviceBrand: $deviceBrand
        deviceOsVersion: $deviceOsVersion
        deviceVersion: $deviceVersion
        password: $password
    ) {
        res
        msg
        hash
        refreshToken
        legals
    }
}
"""


SEND_OTP_MUTATION = """
mutation mkSendOTP($recordId: Int!, $otpHash: String!) {
    xSSendOtp(recordId: $recordId, otpHash: $otpHash) {
        res
        msg
    }
}
"""

OTP_CHALLENGE_TTL_SECONDS = 300.0


class AuthClient(BaseClient):
    """Authentication client for My Verisure API."""

    def __init__(
        self,
        session_manager: SessionManager,
        device_manager: DeviceManager,
    ) -> None:
        """Initialize the authentication client."""
        _LOGGER.debug("AuthClient initialized")
        super().__init__(session_manager=session_manager, profile_context=device_manager.profile_context)
        self._otp_data: Optional[Dict[str, Any]] = None
        self._otp_expires_at: Optional[float] = None
        self._otp_consumed = False
        self._pending_session_data: Optional[dict[str, Any]] = None
        self._pending_hash: Optional[str] = None
        self._pending_refresh_token: Optional[str] = None
        self._pending_user: Optional[str] = None
        self._pending_password: Optional[str] = None
        self._otp_policy = OTPAuthorizationPolicy()
        self._device_manager = device_manager

    def _get_login_headers(self) -> dict[str, str]:
        """Use the native transport for access and refresh token issuance."""
        return {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-MyVerisure/1.0",
            **self._get_native_app_headers(),
        }

    async def login(self, user: str, password: str) -> AuthDTO:
        """Begin native login using this entry's stable device identity."""
        self._otp_data = None
        self._otp_expires_at = None
        self._otp_consumed = False
        self._clear_pending_auth()
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Generate unique ID for this session
        session_id = self._profile_context.current.session_id

        # Prepare variables for the login mutation
        variables: dict[str, Any] = self._device_manager.get_login_variables(session_id)
        variables.update(
            {
                "user": user,
                "password": password,
                "deviceUseBiometric": "DISABLED",
                "phoneAsLogin": False,
            }
        )

        try:
            refreshed = await self._try_refresh_login(user)
            if refreshed is not None:
                return refreshed
            _LOGGER.info("Attempting My Verisure login")
            if should_log_detailed():
                _LOGGER.debug(
                    "Login device context (redacted): %s",
                    redact_sensitive_data(
                        {
                            "uuid": variables.get("uuid"),
                            "deviceName": variables.get("deviceName"),
                        }
                    ),
                )

            # Use direct aiohttp request to control headers/session lifecycle
            result = await self._execute_query_direct(
                LOGIN_MUTATION,
                variables,
                self._get_login_headers(),
            )

            classified = classify_login_response(result)
            if isinstance(classified, LoginResponse):
                login_data = classified.data
                need_device_auth = login_data.get("needDeviceAuthorization")
                if not isinstance(need_device_auth, bool):
                    self._clear_pending_auth()
                    self._clear_otp_challenge()
                    raise MyVerisureAuthenticationError(
                        "Authentication response failed"
                    ) from None
                try:
                    candidate_session_data = build_session_data(
                        user=user,
                        login_data=login_data,
                        login_time=int(time.time()),
                    )
                except MyVerisurePersistenceError:
                    self._clear_pending_auth()
                    self._clear_otp_challenge()
                    raise MyVerisureAuthenticationError(
                        "Authentication response failed"
                    ) from None
                auth_dto = AuthDTO.from_dict(login_data)
                candidate_hash = auth_dto.hash
                candidate_refresh_token = auth_dto.refresh_token
                if not (
                    isinstance(candidate_hash, str) and candidate_hash.strip()
                    or candidate_hash is None and need_device_auth is True
                ):
                    raise MyVerisureAuthenticationError(
                        "Authentication response failed"
                    ) from None
                if candidate_refresh_token is not None and (
                    not isinstance(candidate_refresh_token, str)
                    or not candidate_refresh_token.strip()
                ):
                    raise MyVerisureAuthenticationError(
                        "Authentication response failed"
                    ) from None
                self._pending_session_data = candidate_session_data
                self._pending_hash = candidate_hash
                self._pending_refresh_token = candidate_refresh_token
                self._pending_user = user
                self._pending_password = password

                _LOGGER.info("Login response accepted; checking device authorization")
                if should_log_detailed():
                    _LOGGER.debug(
                        "Session data (redacted): %s",
                        redact_sensitive_data(candidate_session_data),
                    )

                # Check if device authorization is needed before persisting.
                if should_log_detailed():
                    _LOGGER.debug("needDeviceAuthorization=%s", need_device_auth)

                if need_device_auth is True:
                    _LOGGER.info(
                        "Device authorization required — checking authorization state"
                    )
                    try:
                        authorized = await self._check_device_authorization(
                            session_data=candidate_session_data,
                            hash_token=candidate_hash,
                            refresh_token=candidate_refresh_token,
                        )
                    except MyVerisureConnectionError:
                        raise
                    except MyVerisureOTPError as error:
                        _LOGGER.info("Device requires OTP authorization")
                        if error.phones:
                            raise
                        return await self._complete_device_authorization()

                    self._clear_pending_auth()
                    return authorized

                self._clear_pending_auth()
                _LOGGER.debug("Device authorization not required — login complete")
                return auth_dto
            if classified == "Invalid user or password":
                raise MyVerisureAuthenticationError("Invalid user or password") from None
            _LOGGER.error("Login failed")
            raise MyVerisureAuthenticationError("Login failed") from None

        except MyVerisureConnectionError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except asyncio.CancelledError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except MyVerisureOTPError:
            # A well-formed challenge is intentionally returned to the caller;
            # malformed/empty challenges are cleared by _handle_otp_authentication.
            if self._otp_data is None:
                self._clear_pending_auth()
            raise
        except MyVerisureError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except TimeoutError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except (aiohttp.ClientError, OSError):
            self._clear_pending_auth()
            self._clear_otp_challenge()
            _LOGGER.error("Connection to My Verisure failed")
            raise MyVerisureConnectionError("Connection failed") from None
        except ValueError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            _LOGGER.error("Login did not establish a session")
            raise MyVerisureAuthenticationError(
                "Login succeeded without a session hash"
            ) from None
        except Exception:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            _LOGGER.error("Login failed")
            raise MyVerisureAuthenticationError("Login failed") from None

    async def _try_refresh_login(self, user: str) -> AuthDTO | None:
        """Renew an existing native session before using the password again."""
        manager = self._resolve_session_manager()
        token = manager.refresh_token
        if manager.username != user or not isinstance(token, str) or not token.strip():
            return None
        variables: dict[str, Any] = self._device_manager.get_login_variables(self._profile_context.current.session_id)
        variables["refreshToken"] = token
        _LOGGER.info("Renewing the native session with its refresh token")
        result = await self._execute_query_direct(
            REFRESH_LOGIN_MUTATION, variables, self._get_login_headers()
        )
        # A rejected refresh may fall back once to normal device login. Transport
        # failures propagate, avoiding a second request during connectivity issues.
        if isinstance(result, dict) and isinstance(result.get("errors"), list) and result["errors"]:
            _LOGGER.info("Native renewal rejected; attempting registered-device login")
            return None
        wrapper = result.get("data") if isinstance(result, dict) else None
        payload = wrapper.get("xSRefreshLogin") if isinstance(wrapper, dict) else None
        if not isinstance(payload, dict) or "errors" in result:
            raise MyVerisureAuthenticationError("Session refresh response failed")
        if payload.get("res") != "OK" or payload.get("needDeviceAuthorization") is True:
            return None
        classified = classify_login_response({"data": {"xSLoginToken": payload}})
        if not isinstance(classified, LoginResponse):
            raise MyVerisureAuthenticationError("Session refresh response failed")
        auth = AuthDTO.from_dict(classified.data)
        if (
            auth.need_device_authorization is not False
            or not isinstance(auth.hash, str) or not auth.hash.strip()
            or not isinstance(auth.refresh_token, str) or not auth.refresh_token.strip()
        ):
            raise MyVerisureAuthenticationError("Session refresh response failed")
        _LOGGER.info("Native session renewed and ready for transactional persistence")
        return auth

    def _get_current_auth_state(
        self,
        pending_session_data: Optional[dict[str, Any]] = None,
        pending_hash: Optional[str] = None,
    ) -> tuple[dict[str, Any], Optional[str]]:
        """Read committed state or an explicitly supplied pending projection."""
        if pending_session_data is not None or pending_hash is not None:
            return pending_session_data or {}, pending_hash
        if self._pending_session_data is not None or self._pending_hash is not None:
            return self._pending_session_data or {}, self._pending_hash
        session_manager = self._resolve_session_manager()
        return session_manager.get_current_session_data() or {}, session_manager.hash_token

    def _clear_pending_auth(self) -> None:
        """Discard an uncommitted authentication transaction."""
        self._pending_session_data = None
        self._pending_hash = None
        self._pending_refresh_token = None
        self._pending_user = None
        self._pending_password = None

    def _get_authentication_headers(
        self, session_data: dict[str, Any], hash_token: str | None
    ) -> dict[str, str]:
        """Allow a tokenless context only for the active provider login challenge."""
        if isinstance(hash_token, str) and hash_token.strip():
            return self._get_session_headers(session_data, hash_token)
        if (
            hash_token is not None
            or session_data != self._pending_session_data
            or session_data.get("needDeviceAuthorization") is not True
            or not self._pending_user
            or session_data.get("user") != self._pending_user
            or not self._pending_password
        ):
            raise MyVerisureAuthenticationError("Authentication challenge unavailable")
        headers = self._get_headers()
        headers["auth"] = json.dumps({
            "loginTimestamp": int(time.time() * 1000),
            "user": self._pending_user,
            "id": self._profile_context.current.session_id,
            "country": "ES", "lang": session_data.get("lang", "es"),
            "callby": self._profile_context.current.callby, "hash": None,
        })
        return headers

    def _get_device_validation_variables(self) -> dict[str, Any]:
        """Bind verification to the same native device as the pending login."""
        if self._pending_session_data is not None and self._pending_hash is None:
            if not self._pending_password:
                raise MyVerisureAuthenticationError("Authentication challenge unavailable")
            variables = self._device_manager.get_validation_variables()
            return {**variables, "password": self._pending_password}
        return self._device_manager.get_validation_variables()

    def _clear_otp_challenge(self) -> None:
        """Discard any OTP challenge that must not be reused."""
        self._otp_data = None
        self._otp_expires_at = None
        self._otp_consumed = True

    async def _check_device_authorization(
        self,
        *,
        session_data: Optional[dict[str, Any]] = None,
        hash_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> AuthDTO:
        """Check if device is already authorized without requiring OTP."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Prepare variables for device validation
        variables = self._get_device_validation_variables()

        try:
            _LOGGER.info("Checking if device is already authorized")

            # Use session headers for device validation
            session_data, hash_token = self._get_current_auth_state(
                session_data, hash_token
            )
            session_headers = self._get_authentication_headers(
                session_data, hash_token
            )

            # Use direct aiohttp request to get better control over the response
            result = await self._execute_query_direct(
                VALIDATE_DEVICE_MUTATION,
                variables,
                session_headers,
            )

            decision = classify_device_authorization_response(result)
            if isinstance(decision, DeviceAuthorizationSuccess):
                _LOGGER.info("Device is already authorized — no OTP required")
                authorized_hash = decision.data.get("hash") or hash_token
                if not isinstance(authorized_hash, str) or not authorized_hash.strip():
                    raise MyVerisureAuthenticationError("Device returned no session hash")
                return AuthDTO(
                    res="OK",
                    msg="Device already authorized",
                    hash=authorized_hash,
                    refresh_token=refresh_token,
                    lang=session_data.get("lang"),
                    legals=session_data.get("legals"),
                    change_password=session_data.get("changePassword"),
                    need_device_authorization=False,
                )

            if isinstance(decision, DeviceAuthorizationOTPChallenge):
                if should_log_detailed():
                    _LOGGER.debug(
                        "Device requires authorization (redacted): %s",
                        redact_sensitive_data(decision.data),
                    )
                return await self._handle_otp_authentication(decision.data)

            if isinstance(decision, DeviceAuthorizationFailure):
                raise MyVerisureAuthenticationError("Device authorization failed") from None

            raise MyVerisureAuthenticationError("Device authorization failed") from None

        except MyVerisureConnectionError:
            raise
        except MyVerisureOTPError:
            raise
        except MyVerisureError:
            raise
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except (aiohttp.ClientError, OSError):
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except Exception:
            _LOGGER.warning("Device authorization check failed")
            raise MyVerisureAuthenticationError("Device authorization failed") from None

    async def _complete_device_authorization(self) -> AuthDTO:
        """Complete device authorization process with OTP."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Prepare variables for device validation
        variables = self._get_device_validation_variables()

        try:
            _LOGGER.info("Validating device with My Verisure")

            # Use session headers for device validation
            session_data, hash_token = self._get_current_auth_state()
            session_headers = self._get_authentication_headers(
                session_data, hash_token
            )

            # Use direct aiohttp request to get better control over the response
            result = await self._execute_query_direct(
                VALIDATE_DEVICE_MUTATION,
                variables,
                session_headers,
            )

            decision = classify_device_authorization_response(result)
            if isinstance(decision, DeviceAuthorizationSuccess):
                device_data = decision.data
                _LOGGER.info("Device validation successful")
                auth_dto = AuthDTO.from_dict(device_data)
                if auth_dto.need_device_authorization is not False:
                    raise MyVerisureAuthenticationError(
                        "Device authorization returned an ambiguous state"
                    ) from None
                if not isinstance(auth_dto.hash, str) or not auth_dto.hash.strip():
                    raise MyVerisureAuthenticationError(
                        "Device authorization returned no session hash"
                    ) from None
                if auth_dto.refresh_token is not None and (
                    not isinstance(auth_dto.refresh_token, str)
                    or not auth_dto.refresh_token.strip()
                ):
                    raise MyVerisureAuthenticationError(
                        "Device authorization returned an invalid refresh token"
                    ) from None
                self._clear_pending_auth()
                return auth_dto

            if isinstance(decision, DeviceAuthorizationOTPChallenge):
                if should_log_detailed():
                    _LOGGER.debug(
                        "Device validation requires OTP (redacted): %s",
                        redact_sensitive_data(decision.data),
                    )
                _LOGGER.info("OTP authentication required")
                return await self._handle_otp_authentication(decision.data)

            if isinstance(decision, DeviceAuthorizationFailure):
                _LOGGER.error("Device validation failed")
                raise MyVerisureAuthenticationError("Device authorization failed") from None

            raise MyVerisureAuthenticationError("Device authorization failed") from None

        except MyVerisureError:
            raise
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except (aiohttp.ClientError, OSError):
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except Exception:
            _LOGGER.error("Device authorization failed")
            raise MyVerisureAuthenticationError("Device authorization failed") from None

    async def _handle_otp_authentication(
        self, otp_data: Dict[str, Any]
    ) -> AuthDTO:
        """Handle OTP authentication process."""
        prepared = self._otp_policy.prepare(otp_data)
        if prepared is None:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureOTPError("Invalid OTP data received")

        self._otp_data = {
            "phones": [phone.dict() for phone in prepared.phones],
            "otp_hash": prepared.otp_hash,
        }
        self._otp_expires_at = time.monotonic() + OTP_CHALLENGE_TTL_SECONDS
        self._otp_consumed = False
        if should_log_detailed():
            _LOGGER.debug(
                "OTP flow data (redacted): %s",
                redact_sensitive_data(self._otp_data),
            )

        _LOGGER.info("OTP required — %d phone(s) available for SMS", len(prepared.phones))

        # Don't automatically send OTP - let the config flow handle it
        _LOGGER.debug("Raising OTP error for config flow to continue")
        raise MyVerisureOTPError(
            "OTP authentication required - please select phone number",
            phones=prepared.phones,
            otp_hash=prepared.otp_hash,
        )

    def invalidate_otp_challenge(self) -> None:
        """Clear OTP and pending authentication state without network access."""
        self._clear_pending_auth()
        self._clear_otp_challenge()

    def get_available_phones(self) -> list[PhoneDTO]:
        """Get available phone numbers for OTP."""
        if should_log_detailed():
            _LOGGER.debug(
                "get_available_phones — otp_data (redacted): %s",
                redact_sensitive_data(self._otp_data),
            )
        if not self._otp_data:
            _LOGGER.debug("No OTP data — device may already be authorized")
            return []

        phones = tuple(
            PhoneDTO.from_dict(phone)
            for phone in self._otp_data.get("phones", [])
            if isinstance(phone, dict)
        )
        return list(phones)

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.debug("Selecting OTP phone")

        if not self._otp_data:
            _LOGGER.error("No OTP data available")
            return False

        if isinstance(phone_id, bool) or not isinstance(phone_id, int) or phone_id < 0:
            _LOGGER.error("Selected OTP phone is not available")
            return False

        phones = tuple(
            Phone(
                id=phone["id"],
                phone=phone["phone"],
                record_id=phone.get("record_id"),
            )
            for phone in self._otp_data.get("phones", [])
            if isinstance(phone, dict)
            and isinstance(phone.get("id"), int)
            and isinstance(phone.get("phone"), str)
        )
        selected_phone = self._otp_policy.select_phone(phones, phone_id)

        if selected_phone:
            self._otp_data["selected_phone"] = selected_phone.dict()
            _LOGGER.info("OTP phone selected")
            if should_log_detailed():
                _LOGGER.debug(
                    "Selected phone detail (redacted): %s",
                    redact_sensitive_data(selected_phone),
                )
            return True
        else:
            _LOGGER.error("Selected OTP phone is not available")

        return False

    def _ensure_active_otp_challenge(self) -> Dict[str, Any]:
        """Reject absent, expired, or replayed OTP challenges."""
        if self._otp_data is None:
            raise MyVerisureOTPError("OTP challenge unavailable")
        if self._otp_expires_at is None or time.monotonic() >= self._otp_expires_at:
            raise MyVerisureOTPError("OTP challenge expired")
        if self._otp_consumed:
            raise MyVerisureOTPError("OTP challenge already consumed")
        return self._otp_data

    def _ensure_selected_phone(self, challenge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Require an explicit phone selection bound to the active challenge."""
        selected = challenge_data.get("selected_phone")
        phones = challenge_data.get("phones")
        if not isinstance(selected, dict) or not isinstance(phones, list):
            raise MyVerisureOTPError("OTP phone selection required")
        selected_record_id = selected.get("record_id")
        if not any(
            isinstance(phone, dict)
            and phone.get("record_id") == selected_record_id
            and phone.get("id") == selected.get("id")
            for phone in phones
        ):
            raise MyVerisureOTPError("OTP phone selection is invalid")
        return selected

    def _prepare_otp_verification(self) -> tuple[Dict[str, Any], str]:
        """Validate and bind all local OTP state before provider access."""
        try:
            challenge_data = self._ensure_active_otp_challenge()
            otp_hash = challenge_data.get("otp_hash")
            if not isinstance(otp_hash, str) or not otp_hash.strip():
                raise MyVerisureOTPError(
                    "No OTP hash available. Please send OTP first."
                )
            self._ensure_selected_phone(challenge_data)
            return challenge_data, otp_hash
        except MyVerisureOTPError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        variables = {"recordId": record_id, "otpHash": otp_hash}

        try:
            challenge_data = self._ensure_active_otp_challenge()
            challenge_hash = challenge_data.get("otp_hash")
            if not isinstance(challenge_hash, str) or not challenge_hash.strip():
                raise MyVerisureOTPError("OTP challenge hash unavailable")
            if (
                isinstance(record_id, bool)
                or not isinstance(record_id, int)
                or record_id < 0
            ):
                raise MyVerisureOTPError("Invalid OTP record")
            phones = challenge_data.get("phones")
            if not isinstance(phones, list) or not any(
                isinstance(phone, dict) and phone.get("record_id") == record_id
                for phone in phones
            ):
                raise MyVerisureOTPError("OTP record does not belong to challenge")
            if not isinstance(otp_hash, str) or otp_hash != challenge_hash:
                raise MyVerisureOTPError("OTP challenge hash mismatch")
            selected_phone = self._ensure_selected_phone(challenge_data)
            if selected_phone.get("record_id") != record_id:
                raise MyVerisureOTPError("OTP record does not match selected phone")

            _LOGGER.info("OTP send started")

            # Use direct aiohttp request for OTP
            session_data, hash_token = self._get_current_auth_state()
            if not session_data:
                raise MyVerisureAuthenticationError("Authenticated session unavailable")
            result = await self._execute_query_direct(
                SEND_OTP_MUTATION,
                variables,
                self._get_authentication_headers(session_data, hash_token),
            )

            if "errors" in result:
                raise MyVerisureOTPError("OTP delivery failed")

            # The response structure is {'data': {'xSSendOtp': {...}}}
            data = result.get("data", {})
            otp_response = data.get("xSSendOtp", {})

            if otp_response and otp_response.get("res") == "OK":
                _LOGGER.info("OTP SMS sent successfully")
                if should_log_detailed():
                    _LOGGER.debug("OTP send response received")
                return True
            else:
                if not otp_response:
                    raise MyVerisureOTPError("No response data")
                raise MyVerisureOTPError("OTP delivery failed")

        except MyVerisureError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except asyncio.CancelledError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except TimeoutError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except (aiohttp.ClientError, OSError):
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except Exception:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            _LOGGER.error("OTP send failed")
            raise MyVerisureOTPError("OTP delivery failed") from None

    async def verify_otp(self, otp_code: str) -> AuthDTO:
        """Verify the OTP code received via SMS."""
        _challenge_data, otp_hash = self._prepare_otp_verification()
        if not is_valid_otp_code(otp_code):
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureOTPError("OTP code format invalid")

        _LOGGER.info("OTP verification started")

        try:
            # Use the same device validation mutation but with OTP verification headers
            variables = self._get_device_validation_variables()

            # Get session headers (Auth header)
            session_data, hash_token = self._get_current_auth_state()
            if not session_data:
                raise MyVerisureAuthenticationError("Authenticated session unavailable")
            headers = self._get_authentication_headers(session_data, hash_token)

            # Add Security header for OTP verification
            security_header = {
                "token": otp_code,
                "type": "OTP",
                "otpHash": otp_hash,
            }
            headers["Security"] = json.dumps(security_header)

            result = await self._execute_query_direct(
                VALIDATE_DEVICE_MUTATION, variables, headers
            )

            decision = classify_otp_verification_response(result)
            if isinstance(decision, OTPVerificationFailure):
                _LOGGER.error("OTP verification rejected")
                raise MyVerisureOTPError(
                    decision.message,
                    retryable=decision.retryable,
                    code=decision.code,
                )

            validation_response = decision.data
            # Provider acceptance irreversibly consumes the challenge before any
            # post-verification work that may fail or be cancelled.
            self._clear_otp_challenge()

            _LOGGER.info("OTP verification successful — session updated")

            try:
                if "needDeviceAuthorization" not in validation_response:
                    # The current verification mutation does not select this field. Its
                    # positive OTP response must contain the issued session hash.
                    issued_hash = validation_response.get("hash")
                    if not isinstance(issued_hash, str) or not issued_hash.strip():
                        raise MyVerisureDeviceAuthorizationError(
                            "Device authorization returned no session hash"
                        )
                    # The native app repeats login after web-based SMS verification
                    # to obtain device-bound access and refresh tokens.
                    return await self._perform_post_otp_login()
                # Check if device authorization is still needed
                need_device_authorization = validation_response.get(
                    "needDeviceAuthorization"
                )
                if not isinstance(need_device_authorization, bool):
                    raise MyVerisureDeviceAuthorizationError(
                        "Device authorization result ambiguous"
                    )
                if need_device_authorization:
                    _LOGGER.error(
                        "Device authorization still required after OTP verification"
                    )
                    raise MyVerisureDeviceAuthorizationError(
                        "Device authorization failed"
                    )

                # Now perform a new login to get updated tokens
                _LOGGER.info("Completing post-OTP login for fresh tokens")
                return await self._perform_post_otp_login()
            except BaseException:
                self._clear_pending_auth()
                raise

        except MyVerisureOTPError as error:
            if not error.retryable:
                self._clear_pending_auth()
                self._clear_otp_challenge()
            raise
        except MyVerisureError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except asyncio.CancelledError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise
        except TimeoutError:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except (aiohttp.ClientError, OSError):
            self._clear_pending_auth()
            self._clear_otp_challenge()
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except Exception:
            self._clear_pending_auth()
            self._clear_otp_challenge()
            _LOGGER.error("OTP verification failed")
            raise MyVerisureOTPError("OTP verification failed") from None

    async def _perform_post_otp_login(self) -> AuthDTO:
        """Perform a new login after OTP verification to get updated tokens."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Generate unique ID for this session
        session_manager = self._resolve_session_manager()
        user = self._pending_user or session_manager.username
        if not user:
            raise MyVerisureAuthenticationError("No user data available for post-OTP login")

        password = self._pending_password or session_manager.password
        if not password:
            raise MyVerisureAuthenticationError("No password available for post-OTP login")

        # Prepare variables for the login mutation
        variables: dict[str, Any] = self._device_manager.get_login_variables(self._profile_context.current.session_id)
        variables.update(
            {
                "user": user,
                "password": password,
                "deviceUseBiometric": "DISABLED",
                "phoneAsLogin": False,
            }
        )

        try:
            _LOGGER.info("Performing post-OTP login")
            if should_log_detailed():
                _LOGGER.debug(
                    "Post-OTP device context (redacted): %s",
                    redact_sensitive_data(
                        {
                            "uuid": variables.get("uuid"),
                            "deviceName": variables.get("deviceName"),
                        }
                    ),
                )

            result = await self._execute_query_direct(
                LOGIN_MUTATION,
                variables,
                self._get_login_headers(),
            )

            # Check for GraphQL errors first
            if "errors" in result:
                raise MyVerisureAuthenticationError("Post-OTP login failed") from None

            classified = classify_login_response(result)
            if not isinstance(classified, LoginResponse):
                raise MyVerisureAuthenticationError(classified) from None
            login_data = classified.data
            auth_dto = AuthDTO.from_dict(login_data)
            if auth_dto.need_device_authorization is not False:
                raise MyVerisureDeviceAuthorizationError(
                    "Device authorization failed"
                )
            hash_token = auth_dto.hash
            if not isinstance(hash_token, str) or not hash_token.strip():
                raise MyVerisureAuthenticationError(
                    "Post-OTP login did not return a session hash"
                ) from None
            if auth_dto.refresh_token is not None and (
                not isinstance(auth_dto.refresh_token, str)
                or not auth_dto.refresh_token.strip()
            ):
                raise MyVerisureAuthenticationError(
                    "Post-OTP login returned an invalid refresh token"
                ) from None

            _LOGGER.info("Post-OTP login successful")
            self._clear_pending_auth()
            return auth_dto

        except asyncio.CancelledError:
            raise
        except TimeoutError:
            raise MyVerisureTimeoutError("Authentication request timed out") from None
        except (aiohttp.ClientError, OSError):
            raise MyVerisureConnectionError("Authentication transport failed") from None
        except MyVerisureAuthenticationError:
            raise
        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Post-OTP login failed")
            raise MyVerisureAuthenticationError("Post-OTP login failed") from None

    def get_otp_data(self) -> Optional[Dict[str, Any]]:
        """Get the current OTP data."""
        return self._otp_data.copy() if self._otp_data else None

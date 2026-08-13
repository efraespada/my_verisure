"""Authentication client for My Verisure API."""

import json
import logging
import time
from typing import Any, Dict, Optional

from .base_client import BaseClient
from ..application.auth_response_classifier import LoginResponse, classify_login_response
from .device_manager import DeviceManager
from .exceptions import (
    MyVerisureError,
    MyVerisureAuthenticationError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
)
from .models.dto.auth_dto import AuthDTO, PhoneDTO
from ..session_manager import SessionManager
from ..log_utils import (
    redact_otp_message,
    redact_sensitive_data,
    should_log_detailed,
    truncate_secret,
)

_LOGGER = logging.getLogger(__name__)

# GraphQL mutations
LOGIN_MUTATION = """
mutation mkLoginToken($user: String!, $password: String!, $id: String!, $country: String!, $idDevice: String, $idDeviceIndigitall: String, $deviceType: String, $deviceVersion: String, $deviceResolution: String, $lang: String!, $callby: String!, $uuid: String, $deviceName: String, $deviceBrand: String, $deviceOsVersion: String) {
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

VALIDATE_DEVICE_MUTATION = """
mutation mkValidateDevice($idDevice: String, $idDeviceIndigitall: String, $uuid: String, $deviceName: String, $deviceBrand: String, $deviceOsVersion: String, $deviceVersion: String) {
    xSValidateDevice(
        idDevice: $idDevice
        idDeviceIndigitall: $idDeviceIndigitall
        uuid: $uuid
        deviceName: $deviceName
        deviceBrand: $deviceBrand
        deviceOsVersion: $deviceOsVersion
        deviceVersion: $deviceVersion
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



class AuthClient(BaseClient):
    """Authentication client for My Verisure API."""

    def __init__(
        self,
        session_manager: SessionManager,
        device_manager: DeviceManager,
    ) -> None:
        """Initialize the authentication client."""
        _LOGGER.debug("AuthClient initialized (id=%s)", id(self))
        super().__init__(session_manager=session_manager)
        self._otp_data: Optional[Dict[str, Any]] = None
        self._device_manager = device_manager

    async def login(self, user: str, password: str) -> AuthDTO:
        """Login to My Verisure API (Native App Simulation)."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Generate unique ID for this session
        session_id = f"OWI______________________"

        # Prepare variables for the login mutation
        variables = self._device_manager.get_login_variables(session_id)
        variables.update(
            {
                "user": user,
                "password": password,
            }
        )

        try:
            _LOGGER.info("Attempting My Verisure login")
            if should_log_detailed():
                _LOGGER.debug(
                    "Login device context (redacted): uuid=%s name=%s",
                    variables.get("uuid"),
                    variables.get("deviceName"),
                )

            # Use direct aiohttp request to control headers/session lifecycle
            result = await self._execute_query_direct(
                LOGIN_MUTATION,
                variables,
                self._get_headers(),
            )

            classified = classify_login_response(result)
            if isinstance(classified, LoginResponse):
                login_data = classified.data
                # Store session data
                self._session_data = {
                    "user": user,
                    "lang": login_data.get("lang", "ES"),
                    "legals": login_data.get("legals", False),
                    "changePassword": login_data.get("changePassword", False),
                    "needDeviceAuthorization": login_data.get(
                        "needDeviceAuthorization", False
                    ),
                    "login_time": int(time.time()),
                }

                # Store the hash token if available
                self._hash = login_data.get("hash")
                self._refresh_token = login_data.get("refreshToken")

                _LOGGER.info("Successfully logged in to My Verisure")
                if should_log_detailed():
                    _LOGGER.debug(
                        "Session data (redacted): %s",
                        redact_sensitive_data(self._session_data),
                    )

                # Update SessionManager with new credentials
                session_manager = self._resolve_session_manager()
                if not self._hash:
                    raise MyVerisureAuthenticationError(
                        "Login succeeded without a session hash"
                    )
                if should_log_detailed():
                    _LOGGER.debug(
                        "Updating session for user=%s hash=%s",
                        user,
                        truncate_secret(self._hash),
                    )
                await session_manager.async_update_credentials(
                    user,
                    password,
                    self._hash,
                    self._refresh_token,
                )
                session_manager.clear_service_blocked()
                _LOGGER.debug("SessionManager updated with new credentials")

                # Convert to DTO
                auth_dto = AuthDTO.from_dict(login_data)

                # Check if device authorization is needed
                need_device_auth = login_data.get("needDeviceAuthorization")
                if should_log_detailed():
                    _LOGGER.debug("needDeviceAuthorization=%s", need_device_auth)

                if need_device_auth is True:
                    _LOGGER.info(
                        "Device authorization required — checking authorization state"
                    )
                    # First try to check if device is already authorized
                    try:
                        return await self._check_device_authorization()
                    except MyVerisureOTPError:
                        # Device needs OTP authorization
                        _LOGGER.info("Device requires OTP authorization")
                        return await self._complete_device_authorization()
                    except Exception as e:
                        _LOGGER.info(
                            "Device authorization check failed, proceeding with OTP: %s", e
                        )
                        return await self._complete_device_authorization()
                else:
                    _LOGGER.debug("Device authorization not required — login complete")
                    return auth_dto
            _LOGGER.error("Login failed: %s", classified)
            raise MyVerisureAuthenticationError(str(classified))

        except MyVerisureError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during login: %s", e)
            raise MyVerisureAuthenticationError(f"Login failed: {e}") from e

    async def _check_device_authorization(self) -> AuthDTO:
        """Check if device is already authorized without requiring OTP."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Prepare variables for device validation
        variables = self._device_manager.get_validation_variables()

        try:
            _LOGGER.info("Checking if device is already authorized")

            # Use session headers for device validation
            session_headers = self._get_session_headers(
                self._session_data, self._hash
            )

            # Use direct aiohttp request to get better control over the response
            result = await self._execute_query_direct(
                VALIDATE_DEVICE_MUTATION,
                variables,
                session_headers,
            )

            device_data = result.get("data", {}).get("validateDevice", {})
            _LOGGER.debug("Device validation response: %s", device_data)
            
            if device_data.get("res") == "OK":
                _LOGGER.info("Device is already authorized — no OTP required")
                # Device is authorized, return success
                return AuthDTO(
                    res="OK",
                    msg="Device already authorized",
                    hash=self._hash,
                    refresh_token=self._refresh_token,
                    lang=self._session_data.get("lang"),
                    legals=self._session_data.get("legals"),
                    change_password=self._session_data.get("changePassword"),
                    need_device_authorization=False,
                )
            else:
                # Device needs authorization
                if should_log_detailed():
                    _LOGGER.debug(
                        "Device requires authorization (redacted): %s",
                        redact_sensitive_data(device_data),
                    )
                raise MyVerisureOTPError("Device authorization required")

        except MyVerisureOTPError:
            # Re-raise OTP errors
            raise
        except Exception as e:
            _LOGGER.warning("Device authorization check failed: %s", e)
            raise MyVerisureOTPError(f"Device authorization required: {e}") from e

    async def _complete_device_authorization(self) -> AuthDTO:
        """Complete device authorization process with OTP."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Prepare variables for device validation
        variables = self._device_manager.get_validation_variables()

        try:
            _LOGGER.info("Validating device with My Verisure")

            # Use session headers for device validation
            session_headers = self._get_session_headers(
                self._session_data, self._hash
            )

            # Use direct aiohttp request to get better control over the response
            result = await self._execute_query_direct(
                VALIDATE_DEVICE_MUTATION,
                variables,
                session_headers,
            )

            # Check for successful device validation first
            device_data = result.get("xSValidateDevice", {})
            if device_data and device_data.get("res") == "OK":
                self._hash = device_data.get("hash")
                self._refresh_token = device_data.get("refreshToken")
                _LOGGER.info("Device validation successful")
                return AuthDTO.from_dict(device_data)

            # Check for errors that require OTP
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_data = error.get("data", {})
                auth_code = error_data.get("auth-code")
                auth_type = error_data.get("auth-type")

                if should_log_detailed():
                    _LOGGER.debug(
                        "Device validation error — auth-code=%s auth-type=%s",
                        auth_code,
                        auth_type,
                    )

                if auth_type == "OTP" or auth_code == "10001":
                    _LOGGER.info("OTP authentication required")
                    return await self._handle_otp_authentication(error_data)
                elif auth_code == "10010":
                    _LOGGER.error(
                        "Device validation failed - auth-code 10010: Unauthorized"
                    )
                    raise MyVerisureAuthenticationError(
                        "Device validation failed - unauthorized. This may require additional authentication steps."
                    )
                else:
                    raise MyVerisureAuthenticationError(
                        f"Device validation failed: {error.get('message', 'Unknown error')} (auth-code: {auth_code})"
                    )

            # If we reach here, it's an unexpected error
            error_msg = (
                device_data.get("msg", "Unknown error")
                if device_data
                else "No response data"
            )
            raise MyVerisureAuthenticationError(
                f"Device validation failed: {error_msg}"
            )

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error(
                "Unexpected error during device authorization: %s", e
            )
            if "MyVerisureOTPError" in str(e):
                raise MyVerisureOTPError(f"OTP error: {e}") from e
            else:
                raise MyVerisureAuthenticationError(
                    f"Device authorization failed: {e}"
                ) from e

    async def _handle_otp_authentication(
        self, otp_data: Dict[str, Any]
    ) -> AuthDTO:
        """Handle OTP authentication process."""
        auth_phones = otp_data.get("auth-phones", [])
        otp_hash = otp_data.get("auth-otp-hash")

        if not auth_phones or not otp_hash:
            raise MyVerisureOTPError("Invalid OTP data received")

        # Store OTP data for later use - add otp_hash to each phone
        for phone in auth_phones:
            phone["otp_hash"] = otp_hash
            phone["record_id"] = phone.get("id")  # Use phone ID as record_id
        
        self._otp_data = {"phones": auth_phones, "otp_hash": otp_hash}
        if should_log_detailed():
            _LOGGER.debug(
                "OTP flow data (redacted): %s",
                redact_sensitive_data(self._otp_data),
            )

        _LOGGER.info("OTP required — %d phone(s) available for SMS", len(auth_phones))

        # Don't automatically send OTP - let the config flow handle it
        _LOGGER.debug("Raising OTP error for config flow to continue")
        raise MyVerisureOTPError(
            "OTP authentication required - please select phone number"
        )

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

        phones = self._otp_data.get("phones", [])
        _LOGGER.debug("Found %d phone(s) for OTP", len(phones))
        return [PhoneDTO.from_dict(phone) for phone in phones]

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.debug("Selecting phone ID: %d", phone_id)

        if not self._otp_data:
            _LOGGER.error("No OTP data available")
            return False

        phones = self._otp_data.get("phones", [])
        selected_phone = next(
            (p for p in phones if p.get("id") == phone_id), None
        )

        if selected_phone:
            self._otp_data["selected_phone"] = selected_phone
            _LOGGER.info("OTP phone selected (id=%s)", phone_id)
            if should_log_detailed():
                _LOGGER.debug(
                    "Selected phone detail (redacted): %s",
                    redact_sensitive_data(selected_phone),
                )
            return True
        else:
            _LOGGER.error(
                "Phone ID %d not found in available phones", phone_id
            )

        return False

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        variables = {"recordId": record_id, "otpHash": otp_hash}

        try:
            _LOGGER.info("Sending OTP SMS (record_id=%s)", record_id)
            if should_log_detailed():
                _LOGGER.debug("OTP hash (truncated): %s", truncate_secret(otp_hash))
            
            # Update OTP data with the current hash
            if self._otp_data:
                self._otp_data["otp_hash"] = otp_hash

            # Use direct aiohttp request for OTP
            result = await self._execute_query_direct(
                SEND_OTP_MUTATION,
                variables,
                self._get_session_headers(self._session_data, self._hash),
            )

            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                raise MyVerisureOTPError(
                    f"Failed to send OTP: {error.get('message', 'Unknown error')}"
                )

            # The response structure is {'data': {'xSSendOtp': {...}}}
            data = result.get("data", {})
            otp_response = data.get("xSSendOtp", {})

            if otp_response and otp_response.get("res") == "OK":
                _LOGGER.info("OTP SMS sent successfully")
                if should_log_detailed():
                    _LOGGER.debug("OTP send response: %s", otp_response.get("msg"))
                return True
            else:
                error_msg = (
                    otp_response.get("msg", "Unknown error")
                    if otp_response
                    else "No response data"
                )
                raise MyVerisureOTPError(f"Failed to send OTP: {error_msg}")

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error sending OTP: %s", e)
            raise MyVerisureOTPError(f"Failed to send OTP: {e}") from e

    async def verify_otp(self, otp_code: str) -> AuthDTO:
        """Verify the OTP code received via SMS."""
        if not self._otp_data:
            raise MyVerisureOTPError(
                "No OTP data available. Please send OTP first."
            )

        otp_hash = self._otp_data.get("otp_hash")
        if not otp_hash:
            raise MyVerisureOTPError(
                "No OTP hash available. Please send OTP first."
            )

        _LOGGER.info("Verifying OTP: %s", redact_otp_message())
        if should_log_detailed():
            _LOGGER.debug("OTP hash (truncated): %s", truncate_secret(otp_hash))

        try:
            # Use the same device validation mutation but with OTP verification headers
            variables = self._device_manager.get_validation_variables()

            # Get session headers (Auth header)
            headers = self._get_session_headers(self._session_data, self._hash)

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

            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("OTP verification failed: %s", error_msg)
                raise MyVerisureOTPError(
                    f"OTP verification failed: {error_msg}"
                )

            # Check for successful response
            data = result.get("data", {})
            validation_response = data.get("xSValidateDevice", {})

            if validation_response and validation_response.get("res") == "OK":
                # Store the authentication token from OTP verification
                self._hash = validation_response.get("hash")
                refresh_hash = validation_response.get("refreshToken")

                _LOGGER.info("OTP verification successful — session updated")
                if should_log_detailed():
                    _LOGGER.debug(
                        "Tokens from OTP (truncated): hash=%s refresh=%s",
                        truncate_secret(self._hash),
                        truncate_secret(refresh_hash),
                    )

                # Check if device authorization is still needed
                need_device_authorization = validation_response.get(
                    "needDeviceAuthorization", False
                )

                if need_device_authorization:
                    _LOGGER.error(
                        "Device authorization still required after OTP verification"
                    )
                    raise MyVerisureDeviceAuthorizationError(
                        "Device authorization failed. This device is not authorized and will require "
                        "OTP verification on every login. Please contact My Verisure support to "
                        "authorize this device permanently."
                    )

                # Now perform a new login to get updated tokens
                _LOGGER.info("Completing post-OTP login for fresh tokens")

                try:
                    # Perform a new login to get fresh tokens
                    return await self._perform_post_otp_login()

                except Exception as e:
                    _LOGGER.warning(
                        "Post-OTP login failed (%s); using tokens from OTP step",
                        e,
                    )
                    # Even if post-OTP login fails, we still have valid tokens from OTP verification
                    return AuthDTO.from_dict(validation_response)
            else:
                error_msg = (
                    validation_response.get("msg", "Unknown error")
                    if validation_response
                    else "No response data"
                )
                raise MyVerisureOTPError(
                    f"OTP verification failed: {error_msg}"
                )

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during OTP verification: %s", e)
            raise MyVerisureOTPError(f"OTP verification failed: {e}") from e

    async def _perform_post_otp_login(self) -> AuthDTO:
        """Perform a new login after OTP verification to get updated tokens."""
        # Ensure device identifiers are loaded or generated
        await self._device_manager.async_ensure_device_identifiers()

        # Generate unique ID for this session
        session_id = f"OWI______________________"

        # Get user credentials from session data
        user = self._session_data.get("user")
        if not user:
            raise MyVerisureAuthenticationError("No user data available for post-OTP login")
        
        # We need to get the password from the session manager
        session_manager = self._resolve_session_manager()
        password = session_manager.password
        
        if not password:
            raise MyVerisureAuthenticationError("No password available for post-OTP login")

        # Prepare variables for the login mutation
        variables = self._device_manager.get_login_variables(session_id)
        variables.update(
            {
                "user": user,
                "password": password,
            }
        )

        try:
            _LOGGER.info("Performing post-OTP login")
            if should_log_detailed():
                _LOGGER.debug(
                    "Post-OTP device context: uuid=%s name=%s",
                    variables.get("uuid"),
                    variables.get("deviceName"),
                )

            result = await self._execute_query_direct(
                LOGIN_MUTATION,
                variables,
                self._get_headers(),
            )

            # Check for GraphQL errors first
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_message = error.get("message", "Unknown error")
                _LOGGER.error("Post-OTP login failed: %s", error_message)
                raise MyVerisureAuthenticationError(
                    f"Post-OTP login failed: {error_message}"
                )

            # Check for successful response
            data_wrapper = result.get("data", {})
            login_data = data_wrapper.get("xSLoginToken", {}) if isinstance(data_wrapper, dict) else {}
            if login_data and login_data.get("res") == "OK":
                # Store updated session data
                self._session_data = {
                    "user": user,
                    "lang": login_data.get("lang", "ES"),
                    "legals": login_data.get("legals", False),
                    "changePassword": login_data.get("changePassword", False),
                    "needDeviceAuthorization": login_data.get(
                        "needDeviceAuthorization", False
                    ),
                    "login_time": int(time.time()),
                }

                # Store the updated hash token and refresh token
                self._hash = login_data.get("hash")
                self._refresh_token = login_data.get("refreshToken")

                # Update session data with tokens
                if self._hash:
                    self._session_data["hash"] = self._hash
                if self._refresh_token:
                    self._session_data["refreshToken"] = self._refresh_token


                # Update SessionManager with new credentials
                session_manager = self._resolve_session_manager()
                if not self._hash:
                    raise MyVerisureAuthenticationError(
                        "Post-OTP login succeeded without a session hash"
                    )
                await session_manager.async_update_credentials(
                    user,
                    password,
                    self._hash,
                    self._refresh_token,
                )
                session_manager.clear_service_blocked()
                _LOGGER.info("Post-OTP login successful")

                if should_log_detailed():
                    _LOGGER.debug(
                        "Updated tokens (truncated): hash=%s refresh=%s",
                        truncate_secret(self._hash),
                        truncate_secret(self._refresh_token),
                    )

                return AuthDTO.from_dict(login_data)
            else:
                error_msg = (
                    login_data.get("msg", "Unknown error")
                    if login_data
                    else "No response data"
                )
                _LOGGER.error("Post-OTP login failed: %s", error_msg)
                raise MyVerisureAuthenticationError(
                    f"Post-OTP login failed: {error_msg}"
                )

        except Exception as e:
            _LOGGER.error("Unexpected error during post-OTP login: %s", e)
            raise MyVerisureAuthenticationError(
                f"Post-OTP login failed: {e}"
            ) from e

    # Getters for session data
    def get_hash(self) -> Optional[str]:
        """Get the current hash token."""
        return self._hash

    def get_refresh_token(self) -> Optional[str]:
        """Get the current refresh token."""
        return self._refresh_token

    def get_session_data(self) -> Dict[str, Any]:
        """Get the current session data."""
        return self._session_data.copy()

    def get_otp_data(self) -> Optional[Dict[str, Any]]:
        """Get the current OTP data."""
        return self._otp_data.copy() if self._otp_data else None

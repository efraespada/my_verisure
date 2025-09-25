"""Authentication client for My Verisure API."""

import json
import logging
import time
from typing import Any, Dict, Optional

from gql import gql

from .base_client import BaseClient
from .device_manager import DeviceManager
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureOTPError,
    MyVerisureDeviceAuthorizationError,
)
from .models.dto.auth_dto import AuthDTO, PhoneDTO

_LOGGER = logging.getLogger(__name__)

# GraphQL mutations
LOGIN_MUTATION = gql(
    """
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
)

VALIDATE_DEVICE_MUTATION = gql(
    """
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
)

SEND_OTP_MUTATION = gql(
    """
    mutation mkSendOTP($recordId: Int!, $otpHash: String!) {
        xSSendOtp(recordId: $recordId, otpHash: $otpHash) {
            res
            msg
        }
    }
"""
)


class AuthClient(BaseClient):
    """Authentication client for My Verisure API."""

    def __init__(self, user: str, password: str) -> None:
        """Initialize the authentication client."""
        super().__init__()
        self.user = user
        self.password = password
        self._hash: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._session_data: Dict[str, Any] = {}
        self._otp_data: Optional[Dict[str, Any]] = None
        self._device_manager = DeviceManager(user)

    async def login(self) -> AuthDTO:
        """Login to My Verisure API (Native App Simulation)."""
        # Ensure device identifiers are loaded or generated
        self._device_manager.ensure_device_identifiers()

        # Generate unique ID for this session
        session_id = f"OWI______________________"

        # Prepare variables for the login mutation
        variables = self._device_manager.get_login_variables(session_id)
        variables.update(
            {
                "user": self.user,
                "password": self.password,
            }
        )

        try:
            _LOGGER.warning("Attempting login with native app simulation")
            _LOGGER.warning("Device UUID: %s", variables.get("uuid"))
            _LOGGER.warning("Device Name: %s", variables.get("deviceName"))

            result = await self._execute_query(LOGIN_MUTATION, variables)

            # Check for GraphQL errors first
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_message = error.get("message", "Unknown error")
                error_data = error.get("data", {})

                _LOGGER.error("Login failed: %s", error_message)

                # Check for specific error codes
                if error_data.get("err") == "60091":
                    raise MyVerisureAuthenticationError(
                        "Invalid user or password"
                    )
                else:
                    raise MyVerisureAuthenticationError(
                        f"Login failed: {error_message}"
                    )

            # Check for successful response
            login_data = result.get("xSLoginToken", {})
            if login_data and login_data.get("res") == "OK":
                # Store session data
                self._session_data = {
                    "user": self.user,
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
                _LOGGER.info("Session data: %s", self._session_data)

                # Update other clients with the auth token
                if hasattr(self, '_update_other_clients'):
                    self._update_other_clients(self._hash, self._session_data)

                # Convert to DTO
                auth_dto = AuthDTO.from_dict(login_data)

                # Check if device authorization is needed
                if login_data.get("needDeviceAuthorization"):
                    _LOGGER.info(
                        "Device authorization required - proceeding with device validation"
                    )
                    return await self._complete_device_authorization()

                return auth_dto
            else:
                error_msg = (
                    login_data.get("msg", "Unknown error")
                    if login_data
                    else "No response data"
                )
                _LOGGER.error("Login failed: %s", error_msg)
                raise MyVerisureAuthenticationError(
                    f"Login failed: {error_msg}"
                )

        except MyVerisureError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during login: %s", e)
            raise MyVerisureAuthenticationError(f"Login failed: {e}") from e

    async def _complete_device_authorization(self) -> AuthDTO:
        """Complete device authorization process with OTP."""
        # Ensure device identifiers are loaded or generated
        self._device_manager.ensure_device_identifiers()

        # Prepare variables for device validation
        variables = self._device_manager.get_validation_variables()

        try:
            _LOGGER.info("Validating device...")

            # Use session headers for device validation
            session_headers = self._get_session_headers(
                self._session_data, self._hash
            )

            # Use direct aiohttp request to get better control over the response
            result = await self._execute_query_direct(
                VALIDATE_DEVICE_MUTATION.loc.source.body,
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

                _LOGGER.info(
                    "Device validation error - auth-code: %s, auth-type: %s",
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

        # Store OTP data for later use
        self._otp_data = {"phones": auth_phones, "otp_hash": otp_hash}

        _LOGGER.info("📱 Available phone numbers for OTP:")
        for phone in auth_phones:
            _LOGGER.info("  ID %d: %s", phone.get("id"), phone.get("phone"))

        # Don't automatically send OTP - let the config flow handle it
        raise MyVerisureOTPError(
            "OTP authentication required - please select phone number"
        )

    def get_available_phones(self) -> list[PhoneDTO]:
        """Get available phone numbers for OTP."""
        if not self._otp_data:
            return []

        phones = self._otp_data.get("phones", [])
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
            _LOGGER.info(
                "📞 Phone selected: ID %d - %s",
                phone_id,
                selected_phone.get("phone"),
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
            _LOGGER.warning("=== SENDING OTP ===")
            _LOGGER.warning("Record ID: %s", record_id)
            _LOGGER.warning("OTP Hash: %s", otp_hash)

            # Use direct aiohttp request for OTP
            result = await self._execute_query_direct(
                SEND_OTP_MUTATION.loc.source.body,
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
                _LOGGER.info(
                    "OTP sent successfully: %s", otp_response.get("msg")
                )
                _LOGGER.info(
                    "Please check your phone for the SMS and enter the OTP code"
                )
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

        _LOGGER.warning("=== VERIFYING OTP ===")
        _LOGGER.warning("OTP Code: %s", otp_code)
        _LOGGER.warning("OTP Hash: %s", otp_hash)

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
                VALIDATE_DEVICE_MUTATION.loc.source.body, variables, headers
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

                # Log the tokens from OTP verification
                _LOGGER.warning("=== OTP VERIFICATION SUCCESSFUL ===")
                _LOGGER.warning("Hash Token from OTP: %s", self._hash)
                _LOGGER.warning("Refresh Token from OTP: %s", refresh_hash)

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
                _LOGGER.info(
                    "OTP verification successful! Performing new login to get updated tokens..."
                )

                try:
                    # Perform a new login to get fresh tokens
                    return await self._perform_post_otp_login()

                except Exception as e:
                    _LOGGER.warning(
                        "Post-OTP login failed: %s, but OTP verification was successful",
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
        self._device_manager.ensure_device_identifiers()

        # Generate unique ID for this session
        session_id = f"OWI______________________"

        # Prepare variables for the login mutation
        variables = self._device_manager.get_login_variables(session_id)
        variables.update(
            {
                "user": self.user,
                "password": self.password,
            }
        )

        try:
            _LOGGER.info("Performing post-OTP login to get updated tokens...")
            _LOGGER.info("Device UUID: %s", variables.get("uuid"))
            _LOGGER.info("Device Name: %s", variables.get("deviceName"))

            result = await self._execute_query(LOGIN_MUTATION, variables)

            # Check for GraphQL errors first
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_message = error.get("message", "Unknown error")
                _LOGGER.error("Post-OTP login failed: %s", error_message)
                raise MyVerisureAuthenticationError(
                    f"Post-OTP login failed: {error_message}"
                )

            # Check for successful response
            login_data = result.get("xSLoginToken", {})
            if login_data and login_data.get("res") == "OK":
                # Store updated session data
                self._session_data = {
                    "user": self.user,
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

                # Update other clients with the auth token
                if hasattr(self, '_update_other_clients'):
                    self._update_other_clients(self._hash, self._session_data)

                _LOGGER.info("Post-OTP login successful!")
                _LOGGER.info(
                    "Updated hash token obtained: %s",
                    self._hash[:50] + "..." if self._hash else "None",
                )
                _LOGGER.info(
                    "Updated refresh token obtained: %s",
                    (
                        self._refresh_token[:50] + "..."
                        if self._refresh_token
                        else "None"
                    ),
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

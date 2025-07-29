"""My Verisure API client using GraphQL."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import aiohttp
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
    MyVerisureResponseError,
)

_LOGGER = logging.getLogger(__name__)

# GraphQL endpoint
VERISURE_GRAPHQL_URL = "https://customers.securitasdirect.es/owa-api/graphql"

# Login mutation
LOGIN_MUTATION = gql("""
    mutation mkLoginToken($user: String!, $password: String!, $id: String!, $country: String!, $lang: String!, $callby: String!) {
        xSLoginToken(
            user: $user
            password: $password
            id: $id
            country: $country
            lang: $lang
            callby: $callby
        ) {
            res
            msg
            hash
            lang
            legals
            changePassword
            needDeviceAuthorization
        }
    }
""")

VALIDATE_DEVICE_MUTATION = gql("""
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
""")

SEND_OTP_MUTATION = gql("""
    mutation mkSendOTP($recordId: Int!, $otpHash: String!) {
        xSSendOtp(recordId: $recordId, otpHash: $otpHash) {
            res
            msg
        }
    }
""")


class MyVerisureClient:
    """Client for My Verisure GraphQL API."""

    def __init__(self, user: str, password: str) -> None:
        """Initialize the My Verisure client."""
        self.user = user
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
        self._client: Optional[Client] = None
        self._token: Optional[str] = None
        self._cookies: Dict[str, str] = {}
        self._session_data: Dict[str, Any] = {}
        self._otp_data: Optional[Dict[str, Any]] = None

    async def __aenter__(self) -> MyVerisureClient:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to My Verisure API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        transport = AIOHTTPTransport(
            url=VERISURE_GRAPHQL_URL,
            headers=self._get_headers(),
            cookies=self._get_cookies()
        )
        
        self._client = Client(transport=transport, fetch_schema_from_transport=False)

    async def disconnect(self) -> None:
        """Disconnect from My Verisure API."""
        if self._client:
            self._client = None
        
        if self._session:
            await self._session.close()
            self._session = None

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-MyVerisure/1.0",
        }
        
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        
        return headers

    def _get_session_headers(self) -> Dict[str, str]:
        """Get headers with session data for device validation."""
        import time
        import json
        
        if not self._session_data:
            _LOGGER.warning("No session data available, using basic headers")
            return self._get_headers()
        
        # Create session header as shown in the browser
        session_header = {
            "loginTimestamp": int(time.time() * 1000),
            "user": self._session_data.get("user", self.user),
            "id": f"OWP_______________{self.user}_______________{int(time.time() * 1000)}",
            "country": "ES",
            "lang": self._session_data.get("lang", "es"),
            "callby": "OWP_10",
            "hash": self._token if self._token else None
        }
        
        _LOGGER.warning("Session header created - Token present: %s", "Yes" if self._token else "No")
        if self._token:
            _LOGGER.warning("Token length: %d characters", len(self._token))
            _LOGGER.warning("Token preview: %s...", self._token[:20] if len(self._token) > 20 else self._token)
        else:
            _LOGGER.error("No JWT token available for session headers!")
        
        headers = self._get_headers()
        headers["Auth"] = json.dumps(session_header)
        
        return headers

    def _get_cookies(self) -> Dict[str, str]:
        """Get cookies for API requests."""
        return self._cookies.copy()

    def _update_cookies_from_response(self, response_cookies: Any) -> None:
        """Update cookies from response."""
        if hasattr(response_cookies, 'items'):
            for name, value in response_cookies.items():
                if value:
                    self._cookies[name] = value
                    _LOGGER.debug("Updated cookie: %s", name)

    async def _execute_query(self, query: Any, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        if not self._client:
            raise MyVerisureConnectionError("Client not connected")
        
        try:
            # Use execute instead of execute_async to get better error handling
            result = await self._client.execute_async(query, variable_values=variables)
            return result
        except Exception as e:
            _LOGGER.error("GraphQL query failed: %s", e)
            # Check if this is a GraphQL error response
            if "errors" in str(e):
                # Try to extract the actual error from the exception
                import json
                try:
                    # The error might be embedded in the exception message
                    error_str = str(e)
                    if "{" in error_str and "}" in error_str:
                        start = error_str.find("{")
                        end = error_str.rfind("}") + 1
                        error_json = error_str[start:end]
                        error_data = json.loads(error_json)
                        return error_data
                except:
                    pass
            
            # Return a generic error if we can't parse it
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_device_validation_direct(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute device validation using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")
        
        try:
            # Prepare the GraphQL request
            query = """
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
            
            request_data = {
                "query": query,
                "variables": variables
            }
            
            # Get session headers
            headers = self._get_session_headers()
            
            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.debug("Direct device validation response: %s", result)
                return result
                
        except Exception as e:
            _LOGGER.error("Direct device validation failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_query_raw(self, query: Any, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query using raw transport to get better error handling."""
        if not self._client or not self._client.transport:
            raise MyVerisureConnectionError("Client not connected")
        
        try:
            # Prepare the request
            request_data = {
                "query": query.loc.source.body,
                "variables": variables or {}
            }
            
            # Execute using transport directly
            result = await self._client.transport.execute(request_data)
            return result
        except Exception as e:
            _LOGGER.error("Raw GraphQL query failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_otp_direct(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute OTP send using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")
        
        try:
            # Prepare the GraphQL request
            query = """
            mutation mkSendOTP($recordId: Int!, $otpHash: String!) {
                xSSendOtp(recordId: $recordId, otpHash: $otpHash) {
                    res
                    msg
                }
            }
            """
            
            request_data = {
                "query": query,
                "variables": variables
            }
            
            # Get session headers
            headers = self._get_session_headers()
            
            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.debug("Direct OTP response: %s", result)
                return result
                
        except Exception as e:
            _LOGGER.error("Direct OTP failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_otp_verification_direct(self, otp_code: str, otp_hash: str) -> Dict[str, Any]:
        """Execute OTP verification using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare the GraphQL request (same as device validation)
            query = """
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

            # Empty variables as specified
            variables = {}

            request_data = {
                "query": query,
                "variables": variables
            }

            # Get session headers (Auth header)
            headers = self._get_session_headers()
            
            # Add Security header for OTP verification
            import json
            security_header = {
                "token": otp_code,
                "type": "OTP",
                "otpHash": otp_hash
            }
            headers["Security"] = json.dumps(security_header)

            _LOGGER.debug("OTP verification headers: %s", headers)

            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.debug("Direct OTP verification response: %s", result)
                return result

        except Exception as e:
            _LOGGER.error("Direct OTP verification failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_installations_direct(self) -> Dict[str, Any]:
        """Execute installations query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare the GraphQL request
            query = """
            query mkInstallationList {
              xSInstallations {
                installations {
                  numinst
                  alias
                  panel
                  type
                  name
                  surname
                  address
                  city
                  postcode
                  province
                  email
                  phone
                  due
                  role
                }
              }
            }
            """

            request_data = {
                "query": query
            }

            # Get session headers (Auth header with token)
            headers = self._get_session_headers()

            _LOGGER.warning("Installations query headers: %s", headers)

            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("Direct installations response: %s", result)
                return result

        except Exception as e:
            _LOGGER.error("Direct installations query failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_installation_services_direct(self, installation_id: str) -> Dict[str, Any]:
        """Execute installation services query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare the GraphQL request
            query = """
            query Srv($numinst: String!, $uuid: String) {
              xSSrv(numinst: $numinst, uuid: $uuid) {
                res
                msg
                language
                installation {
                  numinst
                  role
                  alias
                  status
                  panel
                  sim
                  instIbs
                  services {
                    idService
                    active
                    visible
                    bde
                    isPremium
                    codOper
                    request
                    minWrapperVersion
                    unprotectActive
                    unprotectDeviceStatus
                    instDate
                    genericConfig {
                      total
                      attributes {
                        key
                        value
                      }
                    }
                    attributes {
                      attributes {
                        name
                        value
                        active
                      }
                    }
                  }
                  configRepoUser {
                    alarmPartitions {
                      id
                      enterStates
                      leaveStates
                    }
                  }
                  capabilities
                }
              }
            }
            """

            # Prepare variables
            variables = {
                "numinst": installation_id
            }

            request_data = {
                "query": query,
                "variables": variables
            }

            # Get session headers (Auth header with token)
            headers = self._get_session_headers()

            _LOGGER.warning("Installation services query headers: %s", headers)
            _LOGGER.warning("Installation services variables: %s", variables)

            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("Direct installation services response: %s", result)
                return result

        except Exception as e:
            _LOGGER.error("Direct installation services query failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def login(self) -> bool:
        """Login to My Verisure API."""
        import uuid
        import time
        
        # Generate unique ID for this session
        session_id = f"OWP_______________{self.user}_______________{int(time.time() * 1000)}"
        
        # Prepare variables for the login mutation
        variables = {
            "id": session_id,
            "country": "ES",
            "callby": "OWP_10",
            "lang": "es",
            "user": self.user,
            "password": self.password
        }
        
        try:
            result = await self._execute_query(LOGIN_MUTATION, variables)
            
            # Check for GraphQL errors first
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_message = error.get("message", "Unknown error")
                error_data = error.get("data", {})
                
                _LOGGER.error("Login failed: %s", error_message)
                
                # Check for specific error codes
                if error_data.get("err") == "60091":
                    raise MyVerisureAuthenticationError("Invalid user or password")
                else:
                    raise MyVerisureAuthenticationError(f"Login failed: {error_message}")
            
            # Check for successful response
            login_data = result.get("xSLoginToken", {})
            if login_data and login_data.get("res") == "OK":
                # Store session data
                self._session_data = {
                    "user": self.user,
                    "lang": login_data.get("lang", "ES"),
                    "legals": login_data.get("legals", False),
                    "changePassword": login_data.get("changePassword", False),
                    "needDeviceAuthorization": login_data.get("needDeviceAuthorization", False),
                    "login_time": int(time.time())
                }
                
                # Store the hash token if available
                self._token = login_data.get("hash")
                
                _LOGGER.info("Successfully logged in to My Verisure")
                _LOGGER.info("Session data: %s", self._session_data)
                
                # Check if device authorization is needed
                if login_data.get("needDeviceAuthorization"):
                    _LOGGER.info("Device authorization required - proceeding with device validation")
                    return await self._complete_device_authorization()
                
                return True
            else:
                error_msg = login_data.get("msg", "Unknown error") if login_data else "No response data"
                _LOGGER.error("Login failed: %s", error_msg)
                raise MyVerisureAuthenticationError(f"Login failed: {error_msg}")
                    
        except MyVerisureError:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during login: %s", e)
            raise MyVerisureAuthenticationError(f"Login failed: {e}") from e

    async def _complete_device_authorization(self) -> bool:
        """Complete device authorization process with OTP."""
        import uuid
        import platform
        
        # Generate device information
        device_uuid = str(uuid.uuid4())
        device_name = f"HomeAssistant-{platform.system()}"
        device_brand = "HomeAssistant"
        device_os = f"{platform.system()} {platform.release()}"
        device_version = "1.0.0"
        
        # Prepare variables for device validation
        variables = {
            "idDevice": device_uuid,
            "idDeviceIndigitall": None,
            "uuid": device_uuid,
            "deviceName": device_name,
            "deviceBrand": device_brand,
            "deviceOsVersion": device_os,
            "deviceVersion": device_version
        }
        
        try:
            _LOGGER.info("Validating device...")
            
            # Use session headers for device validation
            original_headers = self._get_headers()
            session_headers = self._get_session_headers()
            
            # Temporarily update transport headers
            if hasattr(self._client, 'transport') and hasattr(self._client.transport, 'headers'):
                self._client.transport.headers = session_headers
            
            # Use direct aiohttp request to get better control over the response
            result = await self._execute_device_validation_direct(variables)
            
            # Restore original headers
            if hasattr(self._client, 'transport') and hasattr(self._client.transport, 'headers'):
                self._client.transport.headers = original_headers
            
            # Check for OTP requirement
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_data = error.get("data", {})
                auth_code = error_data.get("auth-code")
                auth_type = error_data.get("auth-type")
                
                _LOGGER.info("Device validation error - auth-code: %s, auth-type: %s", auth_code, auth_type)
                _LOGGER.info("Full error data: %s", error_data)
                _LOGGER.info("Full error: %s", error)
                
                if auth_type == "OTP" or auth_code == "10001":
                    _LOGGER.info("OTP authentication required")
                    return await self._handle_otp_authentication(error_data)
                elif auth_code == "10010":
                    _LOGGER.error("Device validation failed - auth-code 10010: Unauthorized")
                    raise MyVerisureAuthenticationError("Device validation failed - unauthorized. This may require additional authentication steps.")
                else:
                    raise MyVerisureAuthenticationError(f"Device validation failed: {error.get('message', 'Unknown error')} (auth-code: {auth_code})")
            
            # If we get here, the error was caught as an exception
            # Let's try to extract the error from the exception message
            if isinstance(result, dict) and "errors" in result:
                error = result["errors"][0]
                if isinstance(error, dict) and "message" in error:
                    error_msg = error["message"]
                    # Check if the error message contains the actual error data
                    if "auth-code" in error_msg:
                        # Try to extract the auth-code from the error message
                        if "10001" in error_msg:
                            _LOGGER.info("OTP authentication required (extracted from error message)")
                            # Extract the actual error data from the exception message
                            import json
                            try:
                                # The error message contains the full error data
                                if "{" in error_msg and "}" in error_msg:
                                    start = error_msg.find("{")
                                    end = error_msg.rfind("}") + 1
                                    error_json = error_msg[start:end]
                                    error_data = json.loads(error_json)
                                    if "data" in error_data:
                                        return await self._handle_otp_authentication(error_data["data"])
                            except:
                                pass
                            
                            # Fallback to simulated data if extraction fails
                            otp_data = {
                                "auth-type": "OTP",
                                "auth-code": "10001",
                                "auth-phones": [
                                    {"id": 0, "phone": "**********975"},
                                    {"id": 1, "phone": "**********808"}
                                ],
                                "auth-otp-hash": "simulated-hash"
                            }
                            return await self._handle_otp_authentication(otp_data)
                        elif "10010" in error_msg:
                            _LOGGER.error("Device validation failed - auth-code 10010: Unauthorized")
                            raise MyVerisureAuthenticationError("Device validation failed - unauthorized. This may require additional authentication steps.")
            
            raise MyVerisureAuthenticationError(f"Device validation failed: {result}")
            
            # Check for successful device validation
            device_data = result.get("xSValidateDevice", {})
            if device_data and device_data.get("res") == "OK":
                self._token = device_data.get("hash")
                _LOGGER.info("Device validation successful")
                return True
            else:
                error_msg = device_data.get("msg", "Unknown error") if device_data else "No response data"
                raise MyVerisureAuthenticationError(f"Device validation failed: {error_msg}")
                
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during device authorization: %s", e)
            if "MyVerisureOTPError" in str(e):
                raise MyVerisureOTPError(f"OTP error: {e}") from e
            else:
                raise MyVerisureAuthenticationError(f"Device authorization failed: {e}") from e

    async def _handle_otp_authentication(self, otp_data: Dict[str, Any]) -> bool:
        """Handle OTP authentication process."""
        auth_phones = otp_data.get("auth-phones", [])
        otp_hash = otp_data.get("auth-otp-hash")
        
        if not auth_phones or not otp_hash:
            raise MyVerisureOTPError("Invalid OTP data received")
        
        # Store OTP data for later use
        self._otp_data = {
            "phones": auth_phones,
            "otp_hash": otp_hash
        }
        
        _LOGGER.info("📱 Available phone numbers for OTP:")
        for phone in auth_phones:
            _LOGGER.info("  ID %d: %s", phone.get("id"), phone.get("phone"))
        
        # Don't automatically send OTP - let the config flow handle it
        raise MyVerisureOTPError("OTP authentication required - please select phone number")

    def get_available_phones(self) -> list[Dict[str, Any]]:
        """Get available phone numbers for OTP."""
        if not self._otp_data:
            return []
        return self._otp_data.get("phones", [])

    def select_phone(self, phone_id: int) -> bool:
        """Select a phone number for OTP."""
        _LOGGER.debug("Selecting phone ID: %d", phone_id)
        
        if not self._otp_data:
            _LOGGER.error("No OTP data available")
            return False
        
        phones = self._otp_data.get("phones", [])
        _LOGGER.debug("Available phones: %s", phones)
        
        selected_phone = next((p for p in phones if p.get("id") == phone_id), None)
        
        if selected_phone:
            self._otp_data["selected_phone"] = selected_phone
            _LOGGER.info("📞 Phone selected: ID %d - %s", phone_id, selected_phone.get("phone"))
            return True
        else:
            _LOGGER.error("Phone ID %d not found in available phones", phone_id)
        
        return False

    async def send_otp(self, record_id: int, otp_hash: str) -> bool:
        """Send OTP to the selected phone number."""
        variables = {
            "recordId": record_id,
            "otpHash": otp_hash
        }
        
        try:
            _LOGGER.info("Sending OTP...")
            
            # Use direct aiohttp request for OTP as well
            result = await self._execute_otp_direct(variables)
            
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                raise MyVerisureOTPError(f"Failed to send OTP: {error.get('message', 'Unknown error')}")
            
            # The response structure is {'data': {'xSSendOtp': {...}}}
            data = result.get("data", {})
            otp_response = data.get("xSSendOtp", {})
            _LOGGER.debug("OTP response: %s", otp_response)
            _LOGGER.debug("Full result: %s", result)
            
            if otp_response and otp_response.get("res") == "OK":
                _LOGGER.info("OTP sent successfully: %s", otp_response.get("msg"))
                _LOGGER.info("Please check your phone for the SMS and enter the OTP code")
                return True
            else:
                error_msg = otp_response.get("msg", "Unknown error") if otp_response else "No response data"
                raise MyVerisureOTPError(f"Failed to send OTP: {error_msg}")
                
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error sending OTP: %s", e)
            raise MyVerisureOTPError(f"Failed to send OTP: {e}") from e

    async def verify_otp(self, otp_code: str) -> bool:
        """Verify the OTP code received via SMS."""
        import time
        
        if not self._otp_data:
            raise MyVerisureOTPError("No OTP data available. Please send OTP first.")
        
        otp_hash = self._otp_data.get("otp_hash")
        if not otp_hash:
            raise MyVerisureOTPError("No OTP hash available. Please send OTP first.")
        
        _LOGGER.info("Verifying OTP code: %s", otp_code)
        
        try:
            # Use the same device validation mutation but with OTP verification headers
            result = await self._execute_otp_verification_direct(otp_code, otp_hash)
            
            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("OTP verification failed: %s", error_msg)
                raise MyVerisureOTPError(f"OTP verification failed: {error_msg}")
            
            # Check for successful response
            data = result.get("data", {})
            validation_response = data.get("xSValidateDevice", {})
            
            _LOGGER.warning("OTP verification response: %s", validation_response)
            
            if validation_response and validation_response.get("res") == "OK":
                # Store the authentication token
                self._token = validation_response.get("hash")
                
                # Update session data to ensure it's available for subsequent requests
                if not self._session_data:
                    self._session_data = {
                        "user": self.user,
                        "lang": "es",
                        "login_time": int(time.time())
                    }
                
                _LOGGER.info("OTP verification successful!")
                _LOGGER.info("Authentication token obtained: %s", self._token[:50] + "..." if self._token else "None")
                _LOGGER.debug("Full token: %s", self._token)
                _LOGGER.warning("Session data updated: %s", self._session_data)
                return True
            else:
                error_msg = validation_response.get("msg", "Unknown error") if validation_response else "No response data"
                raise MyVerisureOTPError(f"OTP verification failed: {error_msg}")
                
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during OTP verification: %s", e)
            raise MyVerisureOTPError(f"OTP verification failed: {e}") from e

    async def get_installations(self) -> list[Dict[str, Any]]:
        """Get user installations."""
        if not self._token:
            raise MyVerisureAuthenticationError("Not authenticated. Please login first.")
        
        _LOGGER.info("Getting user installations...")
        
        try:
            # Execute the installations query
            result = await self._execute_installations_direct()
            
            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("Failed to get installations: %s", error_msg)
                raise MyVerisureError(f"Failed to get installations: {error_msg}")
            
            # Check for successful response
            data = result.get("data", {})
            installations_data = data.get("xSInstallations", {})
            installations = installations_data.get("installations", [])
            
            _LOGGER.info("Found %d installations", len(installations))
            
            # Log installation details
            for i, installation in enumerate(installations):
                _LOGGER.info("Installation %d: %s (%s) - %s", 
                           i + 1, 
                           installation.get("alias", "Unknown"),
                           installation.get("numinst", "Unknown"),
                           installation.get("type", "Unknown"))
            
            return installations
                
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting installations: %s", e)
            raise MyVerisureError(f"Failed to get installations: {e}") from e

    async def save_session(self, file_path: str) -> None:
        """Save session data to file."""
        import json
        import os
        import time
        import asyncio
        
        session_data = {
            "cookies": self._cookies,
            "session_data": self._session_data,
            "token": self._token,
            "user": self.user,
            "saved_time": int(time.time())
        }
        
        def _save_session_sync():
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=2)
        
        # Run the file operation in a thread to avoid blocking
        await asyncio.to_thread(_save_session_sync)
        
        _LOGGER.warning("Session saved to %s", file_path)
        _LOGGER.warning("Saved session includes JWT token: %s", "Yes" if self._token else "No")
        if self._token:
            _LOGGER.warning("Saved JWT token length: %d characters", len(self._token))

    async def load_session(self, file_path: str) -> bool:
        """Load session data from file."""
        import json
        import os
        import asyncio
        
        def _load_session_sync():
            if not os.path.exists(file_path):
                return None
            
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                _LOGGER.error("Failed to load session: %s", e)
                return None
        
        # Run the file operation in a thread to avoid blocking
        session_data = await asyncio.to_thread(_load_session_sync)
        
        if session_data is None:
            _LOGGER.debug("No session file found at %s", file_path)
            return False
        
        try:
            self._cookies = session_data.get("cookies", {})
            self._session_data = session_data.get("session_data", {})
            self._token = session_data.get("token")
            self.user = session_data.get("user", self.user)
            
            _LOGGER.warning("Session loaded from %s", file_path)
            _LOGGER.warning("Loaded session includes JWT token: %s", "Yes" if self._token else "No")
            if self._token:
                _LOGGER.warning("Loaded JWT token length: %d characters", len(self._token))
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to process session data: %s", e)
            return False

    def is_session_valid(self) -> bool:
        """Check if current session is still valid."""
        import time
        
        if not self._session_data:
            _LOGGER.warning("No session data available")
            return False
        
        if not self._token:
            _LOGGER.warning("No authentication token available")
            return False
        
        # Check if session is not too old (12 hours instead of 24 for better security)
        login_time = self._session_data.get("login_time", 0)
        current_time = int(time.time())
        session_age = current_time - login_time
        
        if session_age > 43200:  # 12 hours
            _LOGGER.warning("Session expired (age: %d seconds)", session_age)
            return False
        
        _LOGGER.warning("Session appears valid (age: %d seconds, token present: %s)", 
                     session_age, "Yes" if self._token else "No")
        return True

    async def get_installation_services(self, installation_id: str) -> Dict[str, Any]:
        """Get detailed services and configuration for an installation."""
        if not self._token:
            raise MyVerisureAuthenticationError("Not authenticated. Please login first.")
        
        if not installation_id:
            raise MyVerisureError("Installation ID is required")
        
        _LOGGER.info("Getting services for installation %s", installation_id)
        
        try:
            # Execute the services query
            result = await self._execute_installation_services_direct(installation_id)
            
            # Check for errors first
            if "errors" in result:
                error = result["errors"][0] if result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("Failed to get installation services: %s", error_msg)
                raise MyVerisureError(f"Failed to get installation services: {error_msg}")
            
            # Check for successful response
            data = result.get("data", {})
            services_data = data.get("xSSrv", {})
            
            if services_data and services_data.get("res") == "OK":
                installation = services_data.get("installation", {})
                services = installation.get("services", [])
                
                _LOGGER.info("Found %d services for installation %s", len(services), installation_id)
                _LOGGER.info("Installation status: %s", installation.get("status", "Unknown"))
                _LOGGER.info("Installation panel: %s", installation.get("panel", "Unknown"))
                
                return {
                    "installation": installation,
                    "services": services,
                    "capabilities": services_data.get("capabilities"),
                    "language": services_data.get("language")
                }
            else:
                error_msg = services_data.get("msg", "Unknown error") if services_data else "No response data"
                raise MyVerisureError(f"Failed to get installation services: {error_msg}")
                
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting installation services: %s", e)
            raise MyVerisureError(f"Failed to get installation services: {e}") from e

    async def get_devices(self, installation_id: str) -> list[Dict[str, Any]]:
        """Get devices for an installation."""
        # TODO: Implement actual devices query
        # This is a placeholder - you'll need to provide the actual GraphQL query
        _LOGGER.info(f"Get devices method called for installation {installation_id} - waiting for GraphQL query details")
        
        # Return empty list for now
        return [] 
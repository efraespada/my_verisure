"""Client for My Verisure GraphQL API."""

import json
import logging
import os
import platform
import time
import uuid
import hashlib
from typing import Any, Dict, Optional

import aiohttp
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
    MyVerisureOTPError,
)

_LOGGER = logging.getLogger(__name__)

# GraphQL endpoint
VERISURE_GRAPHQL_URL = "https://customers.securitasdirect.es/owa-api/graphql"

# Login mutation (Native App Simulation)
LOGIN_MUTATION = gql("""
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
        self._device_identifiers: Optional[Dict[str, str]] = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    def _get_device_identifiers_file(self) -> str:
        """Get the path to the device identifiers file."""
        # Use the same directory as session files
        storage_dir = os.path.expanduser(f"~/.storage")
        if not os.path.exists(storage_dir):
            # Fallback to current directory
            storage_dir = "."
        
        return os.path.join(storage_dir, f"my_verisure_device_{self.user}.json")

    def _generate_device_identifiers(self) -> Dict[str, str]:
        """Generate device identifiers based on user and system info."""
        # Generate consistent device UUID based on user and system info
        device_seed = f"{self.user}_{platform.system()}_{platform.machine()}"
        device_uuid = hashlib.sha256(device_seed.encode()).hexdigest()
        
        # Format as UUID string
        formatted_uuid = device_uuid.upper()[:8] + "-" + device_uuid.upper()[8:12] + "-" + device_uuid.upper()[12:16] + "-" + device_uuid.upper()[16:20] + "-" + device_uuid.upper()[20:32]
        
        # Generate Indigitall UUID (random but consistent for this device)
        indigitall_seed = f"{self.user}_indigitall_{platform.system()}"
        indigitall_uuid = hashlib.sha256(indigitall_seed.encode()).hexdigest()
        formatted_indigitall = indigitall_uuid[:8] + "-" + indigitall_uuid[8:12] + "-" + indigitall_uuid[12:16] + "-" + indigitall_uuid[16:20] + "-" + indigitall_uuid[20:32]
        
        return {
            "idDevice": device_uuid,
            "uuid": formatted_uuid,
            "idDeviceIndigitall": formatted_indigitall,
            "deviceName": f"HomeAssistant-{platform.system()}",
            "deviceBrand": "HomeAssistant",
            "deviceOsVersion": f"{platform.system()} {platform.release()}",
            "deviceVersion": "10.154.0",
            "deviceType": "",
            "deviceResolution": "",
            "generated_time": int(time.time())
        }

    def _load_device_identifiers(self) -> bool:
        """Load device identifiers from file."""
        file_path = self._get_device_identifiers_file()
        
        if not os.path.exists(file_path):
            _LOGGER.warning("No device identifiers file found, will generate new ones")
            return False
        
        try:
            with open(file_path, 'r') as f:
                self._device_identifiers = json.load(f)
            
            _LOGGER.warning("Device identifiers loaded from %s", file_path)
            _LOGGER.warning("Device UUID: %s", self._device_identifiers.get("uuid", "Unknown"))
            return True
            
        except Exception as e:
            _LOGGER.error("Failed to load device identifiers: %s", e)
            return False

    def _save_device_identifiers(self) -> None:
        """Save device identifiers to file."""
        if not self._device_identifiers:
            _LOGGER.warning("No device identifiers to save")
            return
        
        file_path = self._get_device_identifiers_file()
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(self._device_identifiers, f, indent=2)
            
            _LOGGER.warning("Device identifiers saved to %s", file_path)
            
        except Exception as e:
            _LOGGER.error("Failed to save device identifiers: %s", e)

    def _ensure_device_identifiers(self) -> None:
        """Ensure device identifiers are loaded or generated."""
        if self._device_identifiers is None:
            # Try to load existing identifiers
            if not self._load_device_identifiers():
                # Generate new identifiers
                _LOGGER.warning("Generating new device identifiers")
                self._device_identifiers = self._generate_device_identifiers()
                self._save_device_identifiers()

    def get_device_info(self) -> Dict[str, str]:
        """Get current device identifiers information."""
        if not self._device_identifiers:
            self._ensure_device_identifiers()
        
        return {
            "uuid": self._device_identifiers.get("uuid", "Unknown"),
            "device_name": self._device_identifiers.get("deviceName", "Unknown"),
            "device_brand": self._device_identifiers.get("deviceBrand", "Unknown"),
            "device_os": self._device_identifiers.get("deviceOsVersion", "Unknown"),
            "device_version": self._device_identifiers.get("deviceVersion", "Unknown"),
            "generated_time": self._device_identifiers.get("generated_time", 0)
        }

    async def connect(self) -> None:
        """Connect to My Verisure API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        # Use session headers if we have a token, otherwise use basic headers
        if self._token:
            headers = self._get_session_headers()
            _LOGGER.warning("Connecting with session headers (token present)")
        else:
            headers = self._get_headers()
            _LOGGER.warning("Connecting with basic headers (no token)")
        
        transport = AIOHTTPTransport(
            url=VERISURE_GRAPHQL_URL,
            headers=headers,
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
        
        if not self._client:
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
        """Login to My Verisure API (Native App Simulation)."""
        # Ensure device identifiers are loaded or generated
        self._ensure_device_identifiers()
        
        # Generate unique ID for this session
        session_id = f"OWI______________________"
        
        # Prepare variables for the login mutation (using persistent device identifiers)
        variables = {
            "id": session_id,
            "country": "ES",
            "callby": "OWI_10",  # Native app identifier
            "lang": "es",
            "user": self.user,
            "password": self.password,
            "idDevice": self._device_identifiers["idDevice"],
            "idDeviceIndigitall": self._device_identifiers["idDeviceIndigitall"],
            "deviceType": self._device_identifiers["deviceType"],
            "deviceVersion": self._device_identifiers["deviceVersion"],
            "deviceResolution": self._device_identifiers["deviceResolution"],
            "uuid": self._device_identifiers["uuid"],
            "deviceName": self._device_identifiers["deviceName"],
            "deviceBrand": self._device_identifiers["deviceBrand"],
            "deviceOsVersion": self._device_identifiers["deviceOsVersion"]
        }
        
        try:
            _LOGGER.warning("Attempting login with native app simulation")
            _LOGGER.warning("Device UUID: %s", variables.get("uuid"))
            _LOGGER.warning("Device Name: %s", variables.get("deviceName"))
            _LOGGER.warning("Callby: %s", variables.get("callby"))
            _LOGGER.warning("Using persistent device identifiers: %s", "Yes" if self._device_identifiers else "No")
            
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
        # Ensure device identifiers are loaded or generated
        self._ensure_device_identifiers()
        
        # Prepare variables for device validation (using persistent identifiers)
        variables = {
            "idDevice": self._device_identifiers["idDevice"],
            "idDeviceIndigitall": self._device_identifiers["idDeviceIndigitall"],
            "uuid": self._device_identifiers["uuid"],
            "deviceName": self._device_identifiers["deviceName"],
            "deviceBrand": self._device_identifiers["deviceBrand"],
            "deviceOsVersion": self._device_identifiers["deviceOsVersion"],
            "deviceVersion": self._device_identifiers["deviceVersion"]
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
        session_data = {
            "cookies": self._cookies,
            "session_data": self._session_data,
            "token": self._token,
            "user": self.user,
            "device_identifiers": self._device_identifiers,
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
            # Load device identifiers if available
            loaded_identifiers = session_data.get("device_identifiers")
            if loaded_identifiers:
                self._device_identifiers = loaded_identifiers
                _LOGGER.warning("Device identifiers loaded from session")
            else:
                _LOGGER.warning("No device identifiers in session, will generate new ones")

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
        
        # Ensure client is connected
        if not self._client:
            _LOGGER.warning("Client not connected, connecting now...")
            await self.connect()
        
        _LOGGER.info("Getting services for installation %s", installation_id)
        
        try:
            _LOGGER.warning("About to execute installation services query for %s", installation_id)
            # Execute the services query
            result = await self._execute_installation_services_direct(installation_id)
            _LOGGER.warning("Installation services query executed successfully")
            
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
        # Ensure client is connected
        if not self._client:
            _LOGGER.warning("Client not connected, connecting now...")
            await self.connect()
        
        # TODO: Implement actual devices query
        # This is a placeholder - you'll need to provide the actual GraphQL query
        _LOGGER.warning(f"Get devices method called for installation {installation_id} - returning sample data")
        
        # Return sample data for testing
        return [
            {
                "id": "alarm_panel_1",
                "type": "ALARM",
                "status": "DARM",  # Using real My Verisure state
                "active": False,
                "battery": 95,
                "signal": -45,
            },
            {
                "id": "motion_sensor_1",
                "type": "PIR",
                "status": "INACTIVE",
                "active": False,
                "battery": 87,
                "signal": -52,
            },
            {
                "id": "door_sensor_1",
                "type": "DOOR",
                "status": "CLOSED",
                "active": False,
                "battery": 92,
                "signal": -48,
            },
            {
                "id": "temp_sensor_1",
                "type": "TEMPERATURE",
                "status": "ACTIVE",
                "active": True,
                "temperature": 22.5,
                "temperature_unit": "C",
                "battery": 89,
                "signal": -50,
            },
        ]

 
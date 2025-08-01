"""Client for My Verisure GraphQL API."""

import asyncio
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
    MyVerisureDeviceAuthorizationError,
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

CHECK_ALARM_QUERY = gql("""
    query CheckAlarm($numinst: String!, $panel: String!) {
        xSCheckAlarm(numinst: $numinst, panel: $panel) {
            res
            msg
            referenceId
        }
    }
""")

CHECK_ALARM_STATUS_QUERY = gql("""
    query CheckAlarmStatus($numinst: String!, $idService: String!, $panel: String!, $referenceId: String!) {
        xSCheckAlarmStatus(
            numinst: $numinst
            idService: $idService
            panel: $panel
            referenceId: $referenceId
        ) {
            res
            msg
            status
            numinst
            protomResponse
            protomResponseDate
            forcedArmed
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
        self._hash: Optional[str] = None
        self._refresh_token: Optional[str] = None
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

    def _load_alarm_status_config(self) -> Dict[str, Any]:
        """Load alarm status configuration from JSON file."""
        try:
            # Get the directory where this file is located and go up one level to the my_verisure directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "alarm_status.json")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            _LOGGER.debug("Alarm status configuration loaded from %s", config_path)
            return config
            
        except Exception as e:
            _LOGGER.error("Failed to load alarm status configuration: %s", e)
            # Return default empty structure
            return {
                "internal": {
                    "day": {"alarm": []},
                    "night": {"alarm": []},
                    "total": {"alarm": []}
                },
                "external": {"alarm": []}
            }

    def _process_alarm_message(self, message: str) -> Dict[str, Any]:
        """Process alarm message and return status structure."""
        if not message:
            return self._get_default_alarm_status()
        
        config = self._load_alarm_status_config()
        
        # Initialize response structure
        response = {
            "internal": {
                "day": {"status": False},
                "night": {"status": False},
                "total": {"status": False}
            },
            "external": {"status": False}
        }
        
        # Check if message matches any alarm in the configuration
        for section, section_config in config.items():
            if section == "internal":
                for subsection, subsection_config in section_config.items():
                    alarm_messages = subsection_config.get("alarm", [])
                    if message in alarm_messages:
                        response["internal"][subsection]["status"] = True
                        _LOGGER.info("Alarm message '%s' matches %s.%s", message, section, subsection)
            elif section == "external":
                alarm_messages = section_config.get("alarm", [])
                if message in alarm_messages:
                    response["external"]["status"] = True
                    _LOGGER.info("Alarm message '%s' matches %s", message, section)
        
        _LOGGER.debug("Processed alarm message '%s' -> %s", message, response)
        return response

    def _get_default_alarm_status(self) -> Dict[str, Any]:
        """Get default alarm status structure with all statuses as False."""
        return {
            "internal": {
                "day": {"status": False},
                "night": {"status": False},
                "total": {"status": False}
            },
            "external": {"status": False}
        }

    async def connect(self) -> None:
        """Connect to My Verisure API."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        
        # Use session headers if we have a hash, otherwise use basic headers
        if self._hash:
            headers = self._get_session_headers()
            _LOGGER.warning("Connecting with session headers (hash present)")
        else:
            headers = self._get_headers()
            _LOGGER.warning("Connecting with basic headers (no hash)")
        
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

    def _get_native_app_headers(self) -> Dict[str, str]:
        """Get native app headers for better authentication."""
        return {
            "App": '{"origin": "native", "appVersion": "10.154.0"}',
            "Extension": '{"mode": "full"}'
        }

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HomeAssistant-MyVerisure/1.0",
        }
        
        # Add native app headers
        headers.update(self._get_native_app_headers())
        
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
            "id": f"OWI______________________",
            "country": "ES",
            "lang": self._session_data.get("lang", "es"),
            "callby": "OWI_10",
            "hash": self._hash if self._hash else None
        }
        
        _LOGGER.warning("Session header created - Hash present: %s", "Yes" if self._hash else "No")
        if self._hash:
            _LOGGER.warning("Hash length: %d characters", len(self._hash))
            _LOGGER.warning("Hash preview: %s...", self._hash[:20] if len(self._hash) > 20 else self._hash)
        else:
            _LOGGER.error("No JWT hash available for session headers!")
        
        headers = self._get_headers()
        headers["auth"] = json.dumps(session_header)
        
        # Ensure native app headers are present
        headers.update(self._get_native_app_headers())
        
        native_headers = self._get_native_app_headers()
        _LOGGER.warning("Session headers created with native app headers")
        _LOGGER.warning("App header: %s", native_headers.get("App"))
        _LOGGER.warning("Extension header: %s", native_headers.get("Extension"))
        
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
            
            # Log the request details
            _LOGGER.warning("=== DEVICE VALIDATION REQUEST ===")
            _LOGGER.warning("URL: %s", VERISURE_GRAPHQL_URL)
            _LOGGER.warning("Headers: %s", json.dumps(headers, indent=2, default=str))
            _LOGGER.warning("Request Body: %s", json.dumps(request_data, indent=2, default=str))
            _LOGGER.warning("Variables: %s", json.dumps(variables, indent=2, default=str))
            _LOGGER.warning("==================================")
            
            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("=== DEVICE VALIDATION RESPONSE ===")
                _LOGGER.warning("Status: %s", response.status)
                _LOGGER.warning("Response: %s", json.dumps(result, indent=2, default=str))
                _LOGGER.warning("===================================")
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
            
            # Log the request details
            _LOGGER.warning("=== OTP SEND REQUEST ===")
            _LOGGER.warning("URL: %s", VERISURE_GRAPHQL_URL)
            _LOGGER.warning("Headers: %s", json.dumps(headers, indent=2, default=str))
            _LOGGER.warning("Request Body: %s", json.dumps(request_data, indent=2, default=str))
            _LOGGER.warning("Variables: %s", json.dumps(variables, indent=2, default=str))
            _LOGGER.warning("========================")
            
            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("=== OTP SEND RESPONSE ===")
                _LOGGER.warning("Status: %s", response.status)
                _LOGGER.warning("Response: %s", json.dumps(result, indent=2, default=str))
                _LOGGER.warning("=========================")
                return result
                
        except Exception as e:
            _LOGGER.error("Direct OTP failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_otp_verification_direct(self, otp_code: str, otp_hash: str) -> Dict[str, Any]:
        """Execute OTP verification using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Ensure device identifiers are available
            self._ensure_device_identifiers()
            
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

            # Use device identifiers as variables
            variables = {
                "idDevice": self._device_identifiers["idDevice"],
                "idDeviceIndigitall": self._device_identifiers["idDeviceIndigitall"],
                "uuid": self._device_identifiers["uuid"],
                "deviceName": self._device_identifiers["deviceName"],
                "deviceBrand": self._device_identifiers["deviceBrand"],
                "deviceOsVersion": self._device_identifiers["deviceOsVersion"],
                "deviceVersion": self._device_identifiers["deviceVersion"]
            }

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

            # Log the request details
            _LOGGER.warning("=== OTP VERIFICATION REQUEST ===")
            _LOGGER.warning("URL: %s", VERISURE_GRAPHQL_URL)
            _LOGGER.warning("Headers: %s", json.dumps(headers, indent=2, default=str))
            _LOGGER.warning("Request Body: %s", json.dumps(request_data, indent=2, default=str))
            _LOGGER.warning("Security Header: %s", json.dumps(security_header, indent=2, default=str))
            _LOGGER.warning("OTP Code: %s", otp_code)
            _LOGGER.warning("OTP Hash: %s", otp_hash)
            _LOGGER.warning("=================================")

            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("=== OTP VERIFICATION RESPONSE ===")
                _LOGGER.warning("Status: %s", response.status)
                _LOGGER.warning("Response: %s", json.dumps(result, indent=2, default=str))
                _LOGGER.warning("==================================")
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

    async def _execute_alarm_status_check_direct(self, installation_id: str, panel: str, id_service: str, reference_id: str, capabilities: str) -> Dict[str, Any]:
        """Execute alarm status check query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "panel": panel,
                "idService": id_service,
                "referenceId": reference_id
            }

            request_data = {
                "query": CHECK_ALARM_STATUS_QUERY.loc.source.body,
                "variables": variables
            }

            # Get session headers (Auth header with token)
            headers = self._get_session_headers()
            
            # Add alarm-specific headers
            headers["numinst"] = installation_id
            headers["panel"] = panel
            headers["x-capabilities"] = capabilities

            _LOGGER.warning("=== ALARM STATUS CHECK REQUEST ===")
            _LOGGER.warning("URL: %s", VERISURE_GRAPHQL_URL)
            _LOGGER.warning("Headers: %s", json.dumps(headers, indent=2, default=str))
            _LOGGER.warning("Request Body: %s", json.dumps(request_data, indent=2, default=str))
            _LOGGER.warning("Variables: %s", json.dumps(variables, indent=2, default=str))
            _LOGGER.warning("===================================")

            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("=== ALARM STATUS CHECK RESPONSE ===")
                _LOGGER.warning("Status: %s", response.status)
                _LOGGER.warning("Response: %s", json.dumps(result, indent=2, default=str))
                _LOGGER.warning("===================================")
                return result

        except Exception as e:
            _LOGGER.error("Direct alarm status check failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_check_alarm_direct(self, installation_id: str, panel: str, capabilities: str) -> Dict[str, Any]:
        """Execute CheckAlarm query using direct aiohttp request to get referenceId."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "panel": panel
            }

            request_data = {
                "query": CHECK_ALARM_QUERY.loc.source.body,
                "variables": variables
            }

            # Get session headers (Auth header with token)
            headers = self._get_session_headers()
            
            # Add alarm-specific headers
            headers["numinst"] = installation_id
            headers["panel"] = panel
            headers["x-capabilities"] = capabilities

            _LOGGER.warning("=== CHECK ALARM REQUEST ===")
            _LOGGER.warning("URL: %s", VERISURE_GRAPHQL_URL)
            _LOGGER.warning("Headers: %s", json.dumps(headers, indent=2, default=str))
            _LOGGER.warning("Request Body: %s", json.dumps(request_data, indent=2, default=str))
            _LOGGER.warning("Variables: %s", json.dumps(variables, indent=2, default=str))
            _LOGGER.warning("===========================")

            # Make direct request
            async with self._session.post(
                VERISURE_GRAPHQL_URL,
                json=request_data,
                headers=headers
            ) as response:
                result = await response.json()
                _LOGGER.warning("=== CHECK ALARM RESPONSE ===")
                _LOGGER.warning("Status: %s", response.status)
                _LOGGER.warning("Response: %s", json.dumps(result, indent=2, default=str))
                _LOGGER.warning("============================")
                return result

        except Exception as e:
            _LOGGER.error("Direct check alarm failed: %s", e)
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
            native_headers = self._get_native_app_headers()
            _LOGGER.warning("Using native app headers: App=%s, Extension=%s", 
                           native_headers.get("App"), 
                           native_headers.get("Extension"))
            
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
                self._hash = login_data.get("hash")
                self._refresh_token = login_data.get("refreshToken")
                
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
            
            # Check for successful device validation first
            device_data = result.get("xSValidateDevice", {})
            if device_data and device_data.get("res") == "OK":
                self._hash = device_data.get("hash")
                self._refresh_token = device_data.get("refreshToken")
                _LOGGER.info("Device validation successful")
                return True
            
            # Check for errors that require OTP
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
            
            # If we get here, check if there are errors in the result that we haven't handled
            if isinstance(result, dict) and "errors" in result:
                error = result["errors"][0]
                if isinstance(error, dict) and "message" in error:
                    error_msg = error["message"]
                    # Check if the error message contains auth-code information
                    if "auth-code" in error_msg:
                        if "10001" in error_msg:
                            _LOGGER.info("OTP authentication required (extracted from error message)")
                            # Try to extract the actual error data from the exception message
                            import json
                            try:
                                if "{" in error_msg and "}" in error_msg:
                                    start = error_msg.find("{")
                                    end = error_msg.rfind("}") + 1
                                    error_json = error_msg[start:end]
                                    error_data = json.loads(error_json)
                                    if "data" in error_data:
                                        return await self._handle_otp_authentication(error_data["data"])
                            except:
                                pass
                        elif "10010" in error_msg:
                            _LOGGER.error("Device validation failed - auth-code 10010: Unauthorized")
                            raise MyVerisureAuthenticationError("Device validation failed - unauthorized. This may require additional authentication steps.")
            
            # If we reach here, it's an unexpected error
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
            _LOGGER.warning("=== SENDING OTP ===")
            _LOGGER.warning("Record ID: %s", record_id)
            _LOGGER.warning("OTP Hash: %s", otp_hash)
            _LOGGER.warning("Variables: %s", json.dumps(variables, indent=2, default=str))
            _LOGGER.warning("==================")
            
            # Use direct aiohttp request for OTP as well
            result = await self._execute_otp_direct(variables)
            
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                raise MyVerisureOTPError(f"Failed to send OTP: {error.get('message', 'Unknown error')}")
            
            # The response structure is {'data': {'xSSendOtp': {...}}}
            data = result.get("data", {})
            otp_response = data.get("xSSendOtp", {})
            _LOGGER.warning("OTP response: %s", json.dumps(otp_response, indent=2, default=str))
            _LOGGER.warning("Full result: %s", json.dumps(result, indent=2, default=str))
            
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
        
        _LOGGER.warning("=== VERIFYING OTP ===")
        _LOGGER.warning("OTP Code: %s", otp_code)
        _LOGGER.warning("OTP Hash: %s", otp_hash)
        _LOGGER.warning("OTP Data: %s", json.dumps(self._otp_data, indent=2, default=str))
        _LOGGER.warning("=====================")
        
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
                # Store the authentication token from OTP verification
                self._hash = validation_response.get("hash")
                refresh_hash = validation_response.get("refreshToken")
                
                # Log the tokens from OTP verification
                _LOGGER.warning("=== OTP VERIFICATION SUCCESSFUL ===")
                _LOGGER.warning("Hash Token from OTP: %s", self._hash)
                _LOGGER.warning("Refresh Token from OTP: %s", refresh_hash)
                _LOGGER.warning("Hash Token Length: %d characters", len(self._hash) if self._hash else 0)
                _LOGGER.warning("Refresh Token Length: %d characters", len(refresh_hash) if refresh_hash else 0)
                _LOGGER.warning("=====================================")
                
                # Check if device authorization is still needed
                need_device_authorization = validation_response.get("needDeviceAuthorization", False)
                _LOGGER.warning("Need device authorization status after OTP verification: %s", need_device_authorization)
                
                if need_device_authorization:
                    _LOGGER.error("Device authorization still required after OTP verification")
                    _LOGGER.error("This device is not authorized and will require OTP on every login")
                    raise MyVerisureDeviceAuthorizationError(
                        "Device authorization failed. This device is not authorized and will require "
                        "OTP verification on every login. Please contact My Verisure support to "
                        "authorize this device permanently."
                    )
                
                # Now perform a new login to get updated tokens
                _LOGGER.info("OTP verification successful! Performing new login to get updated tokens...")
                
                try:
                    # Perform a new login to get fresh tokens
                    login_success = await self._perform_post_otp_login()
                    
                    if login_success:
                        _LOGGER.info("Post-OTP login successful!")
                        _LOGGER.info("Device authorization status: %s", "Authorized" if not need_device_authorization else "Not Authorized")
                        _LOGGER.info("Updated authentication token obtained: %s", self._hash[:50] + "..." if self._hash else "None")
                        _LOGGER.debug("Full updated token: %s", self._hash)
                        _LOGGER.warning("Updated session data: %s", self._session_data)
                        return True
                    else:
                        _LOGGER.warning("Post-OTP login failed, but OTP verification was successful")
                        # Even if post-OTP login fails, we still have valid tokens from OTP verification
                        return True
                        
                except Exception as e:
                    _LOGGER.warning("Post-OTP login failed: %s, but OTP verification was successful", e)
                    # Even if post-OTP login fails, we still have valid tokens from OTP verification
                    return True
            else:
                error_msg = validation_response.get("msg", "Unknown error") if validation_response else "No response data"
                raise MyVerisureOTPError(f"OTP verification failed: {error_msg}")
                
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error during OTP verification: %s", e)
            raise MyVerisureOTPError(f"OTP verification failed: {e}") from e

    async def _perform_post_otp_login(self) -> bool:
        """Perform a new login after OTP verification to get updated tokens."""
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
            _LOGGER.info("Performing post-OTP login to get updated tokens...")
            _LOGGER.info("Device UUID: %s", variables.get("uuid"))
            _LOGGER.info("Device Name: %s", variables.get("deviceName"))
            
            result = await self._execute_query(LOGIN_MUTATION, variables)
            
            # Check for GraphQL errors first
            if "errors" in result and result["errors"]:
                error = result["errors"][0]
                error_message = error.get("message", "Unknown error")
                _LOGGER.error("Post-OTP login failed: %s", error_message)
                return False
            
            # Check for successful response
            login_data = result.get("xSLoginToken", {})
            if login_data and login_data.get("res") == "OK":
                # Store updated session data
                self._session_data = {
                    "user": self.user,
                    "lang": login_data.get("lang", "ES"),
                    "legals": login_data.get("legals", False),
                    "changePassword": login_data.get("changePassword", False),
                    "needDeviceAuthorization": login_data.get("needDeviceAuthorization", False),
                    "login_time": int(time.time())
                }
                
                # Store the updated hash token and refresh token
                self._hash = login_data.get("hash")
                self._refresh_token = login_data.get("refreshToken")
                
                # Update session data with tokens
                if self._hash:
                    self._session_data["hash"] = self._hash
                if self._refresh_token:
                    self._session_data["refreshToken"] = self._refresh_token
                
                _LOGGER.info("Post-OTP login successful!")
                _LOGGER.info("Updated hash token obtained: %s", self._hash[:50] + "..." if self._hash else "None")
                _LOGGER.info("Updated refresh token obtained: %s", self._refresh_token[:50] + "..." if self._refresh_token else "None")
                _LOGGER.info("Device authorization required: %s", login_data.get("needDeviceAuthorization", False))
                
                return True
            else:
                error_msg = login_data.get("msg", "Unknown error") if login_data else "No response data"
                _LOGGER.error("Post-OTP login failed: %s", error_msg)
                return False
                    
        except Exception as e:
            _LOGGER.error("Unexpected error during post-OTP login: %s", e)
            return False



    async def get_installations(self) -> list[Dict[str, Any]]:
        """Get user installations."""
        if not self._hash:
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
            "token": self._hash,  # Keep for backward compatibility
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
        _LOGGER.warning("Saved session includes JWT token: %s", "Yes" if self._hash else "No")
        if self._hash:
            _LOGGER.warning("Saved JWT token length: %d characters", len(self._hash))
        
        # Log tokens if available
        hash_hash = self._session_data.get("hash") if self._session_data else None
        refresh_hash = self._session_data.get("refreshToken") if self._session_data else None
        
        _LOGGER.warning("Saved session includes hash token: %s", "Yes" if hash_hash else "No")
        if hash_hash:
            _LOGGER.warning("Saved hash token length: %d characters", len(hash_hash))
            _LOGGER.warning("Hash token preview: %s...", hash_hash[:20] if len(hash_hash) > 20 else hash_hash)
        
        _LOGGER.warning("Saved session includes refresh token: %s", "Yes" if refresh_hash else "No")
        if refresh_hash:
            _LOGGER.warning("Saved refresh token length: %d characters", len(refresh_hash))
            _LOGGER.warning("Refresh token preview: %s...", refresh_hash[:20] if len(refresh_hash) > 20 else refresh_hash)

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
            # Load token from session data first, then fallback to legacy token field
            self._hash = self._session_data.get("hash")
            self.user = session_data.get("user", self.user)
            # Load device identifiers if available
            loaded_identifiers = session_data.get("device_identifiers")
            if loaded_identifiers:
                self._device_identifiers = loaded_identifiers
                _LOGGER.warning("Device identifiers loaded from session")
            else:
                _LOGGER.warning("No device identifiers in session, will generate new ones")

            _LOGGER.warning("Session loaded from %s", file_path)
            _LOGGER.warning("Loaded session includes JWT token: %s", "Yes" if self._hash else "No")
            if self._hash:
                _LOGGER.warning("Loaded JWT token length: %d characters", len(self._hash))
            
            # Log tokens if available
            hash_hash = self._session_data.get("hash") if self._session_data else None
            refresh_hash = self._session_data.get("refreshToken") if self._session_data else None
            
            _LOGGER.warning("Loaded session includes hash token: %s", "Yes" if hash_hash else "No")
            if hash_hash:
                _LOGGER.warning("Loaded hash token length: %d characters", len(hash_hash))
                _LOGGER.warning("Hash token preview: %s...", hash_hash[:20] if len(hash_hash) > 20 else hash_hash)
            
            _LOGGER.warning("Loaded session includes refresh token: %s", "Yes" if refresh_hash else "No")
            if refresh_hash:
                _LOGGER.warning("Loaded refresh token length: %d characters", len(refresh_hash))
                _LOGGER.warning("Refresh token preview: %s...", refresh_hash[:20] if len(refresh_hash) > 20 else refresh_hash)
            
            return True

        except Exception as e:
            _LOGGER.error("Failed to process session data: %s", e)
            return False

    def is_session_valid(self) -> bool:
        """Check if current session is still valid."""
        if not self._session_data:
            _LOGGER.warning("No session data available")
            return False
        
        if not self._hash:
            _LOGGER.warning("No authentication token available")
            return False
        
        # Check if session is not too old
        login_time = self._session_data.get("login_time", 0)
        current_time = int(time.time())
        session_age = current_time - login_time
        
        if session_age > 360:  # 6 minutes
            _LOGGER.warning("Session expired (age: %d seconds)", session_age)
            return False
        
        _LOGGER.warning("Session appears valid (age: %d seconds, token present: %s)", 
                     session_age, "Yes" if self._hash else "No")
        return True

    async def get_installation_services(self, installation_id: str) -> Dict[str, Any]:
        """Get detailed services and configuration for an installation."""
        if not self._hash:
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
                    "capabilities": installation.get("capabilities"),
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

    async def get_alarm_status(self, installation_id: str, capabilities: str) -> Dict[str, Any]:
        """Get alarm status from installation services and real-time check."""
        if not self._hash:
            raise MyVerisureAuthenticationError("Not authenticated. Please login first.")
        
        if not installation_id:
            raise MyVerisureError("Installation ID is required")
        
        # Ensure client is connected
        if not self._client:
            _LOGGER.warning("Client not connected, connecting now...")
            await self.connect()
        
        _LOGGER.info("Getting alarm status for installation %s", installation_id)
        
        try:
            # Get installation services first
            services_data = await self.get_installation_services(installation_id)
            services = services_data.get("services", [])
            installation = services_data.get("installation", {})
            
            # Try to get real-time alarm status for EST service
            try:
                # Prepare parameters for real-time alarm status check
                panel = installation.get("panel")
                
                # Find EST service for alarm status check
                est_service = None
                for service in services:
                    if service.get("request") == "EST" and service.get("active"):
                        est_service = service
                        _LOGGER.info("Found EST service with idService: %s", service.get("idService"))
                        break
                
                if est_service:
                    service_id = est_service.get("idService")
                    service_request = est_service.get("request")
                    
                    _LOGGER.info("Getting real-time alarm status for EST service: %s (request: %s)", service_id, service_request)
                    
                    # First, get the referenceId for the alarm status check
                    check_alarm_result = await self._execute_check_alarm_direct(installation_id, panel, capabilities)
                    
                    # Check for errors in the CheckAlarm response
                    if "errors" in check_alarm_result:
                        error = check_alarm_result["errors"][0] if check_alarm_result["errors"] else {}
                        error_msg = error.get("message", "Unknown error")
                        _LOGGER.error("Failed to get referenceId: %s", error_msg)
                        return self._get_default_alarm_status()
                    
                    # Check for successful response
                    data = check_alarm_result.get("data", {})
                    check_alarm_data = data.get("xSCheckAlarm", {})
                    
                    if check_alarm_data.get("res") != "OK":
                        error_msg = check_alarm_data.get("msg", "Unknown error")
                        _LOGGER.warning("Could not get referenceId for real-time alarm status check: %s", error_msg)
                        return self._get_default_alarm_status()
                    
                    reference_id = check_alarm_data.get("referenceId")
                    if not reference_id:
                        _LOGGER.warning("No referenceId received from CheckAlarm query")
                        return self._get_default_alarm_status()
                    
                    _LOGGER.info("Obtained referenceId: %s", reference_id)

                    alarm_message = await self._get_real_time_alarm_status(
                        numinst=installation_id,
                        panel=panel,
                        id_service=service_id,
                        reference_id=reference_id,
                        capabilities=capabilities,
                    )
                    
                    # Process the alarm message and return the structured response
                    if alarm_message:
                        _LOGGER.info("Received alarm message: %s", alarm_message)
                        return self._process_alarm_message(alarm_message)
                    else:
                        _LOGGER.warning("No alarm message received")
                        return self._get_default_alarm_status()
                else:
                    _LOGGER.warning("EST service not found or not active, cannot get real-time status")
                    return self._get_default_alarm_status()
                    
            except Exception as e:
                _LOGGER.warning("Error getting real-time alarm status: %s, using service-based status", e)
                return self._get_default_alarm_status()
            
        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting alarm status: %s", e)
            raise MyVerisureError(f"Failed to get alarm status: {e}") from e

    async def _get_real_time_alarm_status(self, numinst: str, panel: str, id_service: str, reference_id: str, capabilities: str) -> str:
        """Get real-time alarm status using the CheckAlarmStatus query with polling."""
        try:
            _LOGGER.info("Getting real-time alarm status with numinst: %s, panel: %s, idService: %s, referenceId: %s", 
                        numinst, panel, id_service, reference_id)
            
            # Poll for alarm status with retries
            max_retries = 10  # Maximum number of retries
            retry_count = 0
            
            while retry_count < max_retries:
                # Execute the alarm status check query
                result = await self._execute_alarm_status_check_direct(
                    installation_id=numinst,
                    panel=panel,
                    id_service=id_service,
                    reference_id=reference_id,
                    capabilities=capabilities
                )
                
                # Check for errors
                if "errors" in result:
                    error = result["errors"][0] if result["errors"] else {}
                    error_msg = error.get("message", "Unknown error")
                    _LOGGER.error("Real-time alarm status check failed: %s", error_msg)
                    return {}
                
                # Check for successful response
                data = result.get("data", {})
                alarm_status_data = data.get("xSCheckAlarmStatus", {})
                res = alarm_status_data.get("res", "Unknown")
                msg = alarm_status_data.get("msg", "Unknown")
                
                _LOGGER.debug("Alarm status check attempt %d: res=%s, msg=%s", retry_count + 1, res, msg)
                
                if res == "OK":                    
                    return msg
                    
                elif res == "KO":
                    # Failed
                    error_msg = alarm_status_data.get("msg", "Unknown error")
                    _LOGGER.error("Real-time alarm status check failed: %s", error_msg)
                    return msg
                    
                elif res == "WAIT":
                    # Need to wait and retry
                    retry_count += 1
                    if retry_count < max_retries:
                        _LOGGER.debug("Alarm status check returned WAIT, waiting 2 seconds before retry %d", retry_count + 1)
                        await asyncio.sleep(5)  # Wait 2 seconds before retry
                    else:
                        _LOGGER.warning("Max retries reached for alarm status check")
                        return None
                else:
                    # Unknown response
                    _LOGGER.warning("Unknown response from alarm status check: res=%s, msg=%s", res, msg)
                    return None
                
        except Exception as e:
            _LOGGER.error("Unexpected error getting real-time alarm status: %s", e)
            return None


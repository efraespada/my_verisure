"""Alarm client for My Verisure API."""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

from gql import gql

from .base_client import BaseClient
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureError,
)


_LOGGER = logging.getLogger(__name__)

# GraphQL queries and mutations
CHECK_ALARM_QUERY = gql(
    """
    query CheckAlarm($numinst: String!, $panel: String!) {
        xSCheckAlarm(numinst: $numinst, panel: $panel) {
            res
            msg
            referenceId
        }
    }
"""
)

ARM_PANEL_MUTATION = gql(
    """
    mutation xSArmPanel(
        $numinst: String!,
        $request: ArmCodeRequest!,
        $panel: String!,
        $currentStatus: String,
        $forceArmingRemoteId: String,
        $armAndLock: Boolean
    ) {
        xSArmPanel(
            numinst: $numinst
            request: $request
            panel: $panel
            currentStatus: $currentStatus
            forceArmingRemoteId: $forceArmingRemoteId
            armAndLock: $armAndLock
        ) {
            res
            msg
            referenceId
        }
    }
"""
)

ARM_STATUS_QUERY = gql(
    """
    query ArmStatus(
        $numinst: String!,
        $request: ArmCodeRequest,
        $panel: String!,
        $referenceId: String!,
        $counter: Int!,
        $forceArmingRemoteId: String,
        $armAndLock: Boolean
    ) {
        xSArmStatus(
            numinst: $numinst
            panel: $panel
            referenceId: $referenceId
            counter: $counter
            request: $request
            forceArmingRemoteId: $forceArmingRemoteId
            armAndLock: $armAndLock
        ) {
            res
            msg
            status
            protomResponse
            protomResponseDate
            numinst
            requestId
            error {
                code
                type
                allowForcing
                exceptionsNumber
                referenceId
                suid
            }
            smartlockStatus {
                state
                deviceId
                updatedOnArm
            }
        }
    }
"""
)

DISARM_PANEL_MUTATION = gql(
    """
    mutation xSDisarmPanel(
        $numinst: String!,
        $request: DisarmCodeRequest!,
        $panel: String!
    ) {
        xSDisarmPanel(numinst: $numinst, request: $request, panel: $panel) {
            res
            msg
            referenceId
        }
    }
"""
)

DISARM_STATUS_QUERY = gql(
    """
    query DisarmStatus(
        $numinst: String!,
        $panel: String!,
        $referenceId: String!,
        $counter: Int!,
        $request: DisarmCodeRequest
    ) {
        xSDisarmStatus(
            numinst: $numinst
            panel: $panel
            referenceId: $referenceId
            counter: $counter
            request: $request
        ) {
            res
            msg
            status
            protomResponse
            protomResponseDate
            numinst
            requestId
            error {
                code
                type
                allowForcing
                exceptionsNumber
                referenceId
                suid
            }
        }
    }
"""
)

CHECK_ALARM_STATUS_QUERY = gql(
    """
    query CheckAlarmStatus(
        $numinst: String!,
        $idService: String!,
        $panel: String!,
        $referenceId: String!
    ) {
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
"""
)


class AlarmClient(BaseClient):
    """Alarm client for My Verisure API."""

    def __init__(self, hash_token: Optional[str] = None, session_data: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the alarm client."""
        super().__init__()
        self._hash = hash_token
        self._session_data = session_data or {}

    def _load_alarm_status_config(self) -> Dict[str, Any]:
        """Load alarm status configuration from JSON file."""
        try:
            # Get the directory where this file is located and go up one level
            # to the my_verisure directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "alarm_status.json")

            with open(config_path, "r") as f:
                config = json.load(f)

            _LOGGER.debug(
                "Alarm status configuration loaded from %s", config_path
            )
            return config

        except Exception as e:
            _LOGGER.error("Failed to load alarm status configuration: %s", e)
            # Return default empty structure
            return {
                "internal": {
                    "day": {"alarm": []},
                    "night": {"alarm": []},
                    "total": {"alarm": []},
                },
                "external": {"alarm": []},
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
                "total": {"status": False},
            },
            "external": {"status": False},
        }

        # Check if message matches any alarm in the configuration
        for section, section_config in config.items():
            if section == "internal":
                for subsection, subsection_config in section_config.items():
                    alarm_messages = subsection_config.get("alarm", [])
                    if message in alarm_messages:
                        response["internal"][subsection]["status"] = True
                        _LOGGER.info(
                            "Alarm message '%s' matches %s.%s",
                            message,
                            section,
                            subsection,
                        )
            elif section == "external":
                alarm_messages = section_config.get("alarm", [])
                if message in alarm_messages:
                    response["external"]["status"] = True
                    _LOGGER.info(
                        "Alarm message '%s' matches %s", message, section
                    )

        _LOGGER.debug("Processed alarm message '%s' -> %s", message, response)
        return response

    def _get_default_alarm_status(self) -> Dict[str, Any]:
        """Get default alarm status structure with all statuses as False."""
        return {
            "internal": {
                "day": {"status": False},
                "night": {"status": False},
                "total": {"status": False},
            },
            "external": {"status": False},
        }

    async def get_alarm_status(
        self,
        installation_id: str,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get alarm status from installation services and real-time check."""
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        if not installation_id:
            raise MyVerisureError("Installation ID is required")

        # Ensure client is connected
        if not self._client:
            _LOGGER.warning("Client not connected, connecting now...")
            await self.connect()

        _LOGGER.info(
            "Getting alarm status for installation %s", installation_id
        )

        try:
            # Try to get real-time alarm status for EST service
            try:
                # Prepare parameters for real-time alarm status check
                panel = "panel1"  # This should come from installation services

                # Find EST service for alarm status check
                # This would normally come from installation services
                # For now, we'll use a default service ID
                service_id = "EST"
                service_request = "EST"

                _LOGGER.info(
                    "Getting real-time alarm status for EST service: %s "
                    "(request: %s)",
                    service_id,
                    service_request,
                )

                # First, get the referenceId for the alarm status check
                check_alarm_result = await self._execute_check_alarm_direct(
                    installation_id,
                    panel,
                    capabilities,
                    hash_token,
                    session_data,
                )

                # Check for errors in the CheckAlarm response
                if "errors" in check_alarm_result:
                    error = (
                        check_alarm_result["errors"][0]
                        if check_alarm_result["errors"]
                        else {}
                    )
                    error_msg = error.get("message", "Unknown error")
                    _LOGGER.error("Failed to get referenceId: %s", error_msg)
                    return self._get_default_alarm_status()

                # Check for successful response
                data = check_alarm_result.get("data", {})
                check_alarm_data = data.get("xSCheckAlarm", {})

                if check_alarm_data.get("res") != "OK":
                    error_msg = check_alarm_data.get("msg", "Unknown error")
                    _LOGGER.warning(
                        "Could not get referenceId for real-time alarm status "
                        "check: %s",
                        error_msg,
                    )
                    return self._get_default_alarm_status()

                reference_id = check_alarm_data.get("referenceId")
                if not reference_id:
                    _LOGGER.warning(
                        "No referenceId received from CheckAlarm query"
                    )
                    return self._get_default_alarm_status()

                _LOGGER.info("Obtained referenceId: %s", reference_id)

                alarm_message = await self._get_real_time_alarm_status(
                    numinst=installation_id,
                    panel=panel,
                    id_service=service_id,
                    reference_id=reference_id,
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

                # Process the alarm message and return the structured response
                if alarm_message:
                    _LOGGER.info("Received alarm message: %s", alarm_message)
                    return self._process_alarm_message(alarm_message)
                else:
                    _LOGGER.warning("No alarm message received")
                    return self._get_default_alarm_status()

            except Exception as e:
                _LOGGER.warning(
                    "Error getting real-time alarm status: %s, using "
                    "service-based status",
                    e,
                )
                return self._get_default_alarm_status()

        except MyVerisureError:
            raise
        except Exception as e:
            _LOGGER.error("Unexpected error getting alarm status: %s", e)
            raise MyVerisureError(f"Failed to get alarm status: {e}") from e

    async def _get_real_time_alarm_status(
        self,
        numinst: str,
        panel: str,
        id_service: str,
        reference_id: str,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Get real-time alarm status using the CheckAlarmStatus query with polling."""
        try:
            _LOGGER.info(
                "Getting real-time alarm status with numinst: %s, panel: %s, "
                "idService: %s, referenceId: %s",
                numinst,
                panel,
                id_service,
                reference_id,
            )

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
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

                # Check for errors
                if "errors" in result:
                    error = result["errors"][0] if result["errors"] else {}
                    error_msg = error.get("message", "Unknown error")
                    _LOGGER.error(
                        "Real-time alarm status check failed: %s", error_msg
                    )
                    return {}

                # Check for successful response
                data = result.get("data", {})
                alarm_status_data = data.get("xSCheckAlarmStatus", {})
                res = alarm_status_data.get("res", "Unknown")
                msg = alarm_status_data.get("msg", "Unknown")

                _LOGGER.debug(
                    "Alarm status check attempt %d: res=%s, msg=%s",
                    retry_count + 1,
                    res,
                    msg,
                )

                if res == "OK":
                    return msg

                elif res == "KO":
                    # Failed
                    error_msg = alarm_status_data.get("msg", "Unknown error")
                    _LOGGER.error(
                        "Real-time alarm status check failed: %s", error_msg
                    )
                    return msg

                elif res == "WAIT":
                    # Need to wait and retry
                    retry_count += 1
                    if retry_count < max_retries:
                        _LOGGER.debug(
                            "Alarm status check returned WAIT, waiting 5 seconds "
                            "before retry %d",
                            retry_count + 1,
                        )
                        await asyncio.sleep(5)  # Wait 5 seconds before retry
                    else:
                        _LOGGER.warning(
                            "Max retries reached for alarm status check"
                        )
                        return None
                else:
                    # Unknown response
                    _LOGGER.warning(
                        "Unknown response from alarm status check: res=%s, msg=%s",
                        res,
                        msg,
                    )
                    return None

        except Exception as e:
            _LOGGER.error(
                "Unexpected error getting real-time alarm status: %s", e
            )
            return None

    async def send_alarm_command(
        self,
        installation_id: str,
        request: str,
        current_status: str = "E",
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send an alarm command to the specified installation using the correct flow."""
        try:
            _LOGGER.info(
                "Sending alarm command '%s' to installation %s",
                request,
                installation_id,
            )

            # Get installation services to get the panel info
            panel = "panel1"  # This should come from installation services
            capabilities = ""  # This should come from installation services

            if not panel:
                _LOGGER.error(
                    "No panel information found for installation %s",
                    installation_id,
                )
                return False

            # Step 1: Send the arm command
            arm_result = await self._execute_arm_panel_direct(
                installation_id=installation_id,
                panel=panel,
                request=request,
                current_status=current_status,
                capabilities=capabilities,
                hash_token=hash_token,
                session_data=session_data,
            )

            # Check for errors in arm command
            if "errors" in arm_result:
                error = arm_result["errors"][0] if arm_result["errors"] else {}
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("Failed to send arm command: %s", error_msg)
                return False

            # Check arm response
            arm_data = arm_result.get("data", {})
            arm_panel_result = arm_data.get("xSArmPanel", {})
            arm_res = arm_panel_result.get("res", "Unknown")
            arm_msg = arm_panel_result.get("msg", "Unknown")
            reference_id = arm_panel_result.get("referenceId")

            if arm_res != "OK" or not reference_id:
                _LOGGER.error(
                    "Failed to send arm command '%s': %s",
                    request,
                    arm_msg,
                )
                return False

            _LOGGER.info(
                "Arm command sent successfully, referenceId: %s", reference_id
            )

            # Step 2: Poll for status until completion
            max_retries = 30  # Maximum number of retries
            retry_count = 0

            while retry_count < max_retries:
                retry_count += 1
                _LOGGER.debug(
                    "Checking arm status, attempt %d/%d",
                    retry_count,
                    max_retries,
                )

                # Execute the status check query
                status_result = await self._execute_arm_status_direct(
                    installation_id=installation_id,
                    panel=panel,
                    request=request,
                    reference_id=reference_id,
                    counter=retry_count,
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

                # Check for errors in status check
                if "errors" in status_result:
                    error = (
                        status_result["errors"][0]
                        if status_result["errors"]
                        else {}
                    )
                    error_msg = error.get("message", "Unknown error")
                    _LOGGER.error("Failed to check arm status: %s", error_msg)
                    return False

                # Check status response
                status_data = status_result.get("data", {})
                arm_status_result = status_data.get("xSArmStatus", {})
                status_res = arm_status_result.get("res", "Unknown")
                status_msg = arm_status_result.get("msg", "Unknown")
                status_status = arm_status_result.get("status")

                _LOGGER.debug(
                    "Arm status check: res=%s, msg=%s, status=%s",
                    status_res,
                    status_msg,
                    status_status,
                )

                if status_res == "OK":
                    _LOGGER.info(
                        "Alarm command '%s' completed successfully: %s",
                        request,
                        status_msg,
                    )
                    return True
                elif status_res == "WAIT":
                    # Need to wait and retry
                    if retry_count < max_retries:
                        _LOGGER.debug(
                            "Arm status returned WAIT, waiting 5 seconds "
                            "before retry"
                        )
                        await asyncio.sleep(5)  # Wait 5 seconds before retry
                    else:
                        _LOGGER.warning(
                            "Max retries reached for arm status check"
                        )
                        return False
                else:
                    # Error or unknown response
                    _LOGGER.error(
                        "Failed to complete alarm command '%s': %s",
                        request,
                        status_msg,
                    )
                    return False

        except Exception as e:
            _LOGGER.error("Unexpected error sending alarm command: %s", e)
            return False

    async def disarm_alarm(
        self,
        installation_id: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Disarm the alarm for the specified installation using the correct flow."""
        try:
            _LOGGER.info(
                "Disarming alarm for installation %s", installation_id
            )

            # Get installation services to get the panel info
            panel = "panel1"  # This should come from installation services
            capabilities = ""  # This should come from installation services

            if not panel:
                _LOGGER.error(
                    "No panel information found for installation %s",
                    installation_id,
                )
                return False

            # Step 1: Send the disarm command
            disarm_result = await self._execute_disarm_panel_direct(
                installation_id=installation_id,
                panel=panel,
                request="DARM1",
                capabilities=capabilities,
                hash_token=hash_token,
                session_data=session_data,
            )

            # Check for errors in disarm command
            if "errors" in disarm_result:
                error = (
                    disarm_result["errors"][0]
                    if disarm_result["errors"]
                    else {}
                )
                error_msg = error.get("message", "Unknown error")
                _LOGGER.error("Failed to send disarm command: %s", error_msg)
                return False

            # Check disarm response
            disarm_data = disarm_result.get("data", {})
            disarm_panel_result = disarm_data.get("xSDisarmPanel", {})
            disarm_res = disarm_panel_result.get("res", "Unknown")
            disarm_msg = disarm_panel_result.get("msg", "Unknown")
            reference_id = disarm_panel_result.get("referenceId")

            if disarm_res != "OK" or not reference_id:
                _LOGGER.error("Failed to send disarm command: %s", disarm_msg)
                return False

            _LOGGER.info(
                "Disarm command sent successfully, referenceId: %s",
                reference_id,
            )

            # Step 2: Poll for status until completion
            max_retries = 30  # Maximum number of retries
            retry_count = 0

            while retry_count < max_retries:
                retry_count += 1
                _LOGGER.debug(
                    "Checking disarm status, attempt %d/%d",
                    retry_count,
                    max_retries,
                )

                # Execute the status check query
                status_result = await self._execute_disarm_status_direct(
                    installation_id=installation_id,
                    panel=panel,
                    request="DARM1",
                    reference_id=reference_id,
                    counter=retry_count,
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

                # Check for errors in status check
                if "errors" in status_result:
                    error = (
                        status_result["errors"][0]
                        if status_result["errors"]
                        else {}
                    )
                    error_msg = error.get("message", "Unknown error")
                    _LOGGER.error(
                        "Failed to check disarm status: %s", error_msg
                    )
                    return False

                # Check status response
                status_data = status_result.get("data", {})
                disarm_status_result = status_data.get("xSDisarmStatus", {})
                status_res = disarm_status_result.get("res", "Unknown")
                status_msg = disarm_status_result.get("msg", "Unknown")
                status_status = disarm_status_result.get("status")
                protom_response = disarm_status_result.get("protomResponse")

                _LOGGER.debug(
                    "Disarm status check: res=%s, msg=%s, status=%s, "
                    "protomResponse=%s",
                    status_res,
                    status_msg,
                    status_status,
                    protom_response,
                )

                if status_res == "OK":
                    _LOGGER.info("Alarm disarmed successfully: %s", status_msg)
                    return True
                elif status_res == "WAIT":
                    # Need to wait and retry
                    if retry_count < max_retries:
                        _LOGGER.debug(
                            "Disarm status returned WAIT, waiting 2 seconds "
                            "before retry"
                        )
                        await asyncio.sleep(5)  # Wait 5 seconds before retry
                    else:
                        _LOGGER.warning(
                            "Max retries reached for disarm status check"
                        )
                        return False
                else:
                    # Error or unknown response
                    _LOGGER.error(
                        "Failed to complete disarm command: %s", status_msg
                    )
                    return False

        except Exception as e:
            _LOGGER.error("Unexpected error disarming alarm: %s", e)
            return False

    async def arm_alarm_away(
        self,
        installation_id: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Arm the alarm in away mode for the specified installation."""
        return await self.send_alarm_command(
            installation_id,
            "ARM1",
            hash_token=hash_token,
            session_data=session_data,
        )

    async def arm_alarm_home(
        self,
        installation_id: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Arm the alarm in home mode for the specified installation."""
        return await self.send_alarm_command(
            installation_id,
            "PERI1",
            hash_token=hash_token,
            session_data=session_data,
        )

    async def arm_alarm_night(
        self,
        installation_id: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Arm the alarm in night mode for the specified installation."""
        return await self.send_alarm_command(
            installation_id,
            "ARMNIGHT1",
            hash_token=hash_token,
            session_data=session_data,
        )

    # Helper methods for direct GraphQL execution
    async def _execute_check_alarm_direct(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute CheckAlarm query using direct aiohttp request to get referenceId."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {"numinst": installation_id, "panel": panel}

            # Get session headers (Auth header with token)
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            # Add alarm-specific headers
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Make direct request
            result = await self._execute_query_direct(
                CHECK_ALARM_QUERY.loc.source.body, variables, headers
            )

            return result

        except Exception as e:
            _LOGGER.error("Direct check alarm failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_alarm_status_check_direct(
        self,
        installation_id: str,
        panel: str,
        id_service: str,
        reference_id: str,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute alarm status check query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "panel": panel,
                "idService": id_service,
                "referenceId": reference_id,
            }

            # Get session headers (Auth header with token)
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            # Add alarm-specific headers
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Make direct request
            result = await self._execute_query_direct(
                CHECK_ALARM_STATUS_QUERY.loc.source.body, variables, headers
            )

            return result

        except Exception as e:
            _LOGGER.error("Direct alarm status check failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_arm_panel_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        current_status: str = "E",
        capabilities: str = "",
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute arm panel mutation using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "request": request,
                "panel": panel,
                "currentStatus": current_status,
                "forceArmingRemoteId": None,
                "armAndLock": False,
            }

            # Get session headers (Auth header with token)
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            # Add alarm-specific headers
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Make direct request
            result = await self._execute_query_direct(
                ARM_PANEL_MUTATION.loc.source.body, variables, headers
            )

            return result

        except Exception as e:
            _LOGGER.error("Direct arm panel failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_arm_status_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
        capabilities: str = "",
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute arm status query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "request": request,
                "panel": panel,
                "referenceId": reference_id,
                "counter": counter,
                "forceArmingRemoteId": None,
                "armAndLock": False,
            }

            # Get session headers (Auth header with token)
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            # Add alarm-specific headers
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Make direct request
            result = await self._execute_query_direct(
                ARM_STATUS_QUERY.loc.source.body, variables, headers
            )

            return result

        except Exception as e:
            _LOGGER.error("Direct arm status failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_disarm_panel_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        capabilities: str = "",
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute disarm panel mutation using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "request": request,
                "panel": panel,
            }

            # Get session headers (Auth header with token)
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            # Add alarm-specific headers
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Make direct request
            result = await self._execute_query_direct(
                DISARM_PANEL_MUTATION.loc.source.body, variables, headers
            )

            return result

        except Exception as e:
            _LOGGER.error("Direct disarm panel failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    async def _execute_disarm_status_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
        capabilities: str = "",
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute disarm status query using direct aiohttp request."""
        if not self._session:
            raise MyVerisureConnectionError("Client not connected")

        try:
            # Prepare variables
            variables = {
                "numinst": installation_id,
                "panel": panel,
                "referenceId": reference_id,
                "counter": counter,
                "request": request,
            }

            # Get session headers (Auth header with token)
            headers = (
                self._get_session_headers(session_data or {}, hash_token)
                if session_data
                else None
            )

            # Add alarm-specific headers
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            # Make direct request
            result = await self._execute_query_direct(
                DISARM_STATUS_QUERY.loc.source.body, variables, headers
            )

            return result

        except Exception as e:
            _LOGGER.error("Direct disarm status failed: %s", e)
            return {"errors": [{"message": str(e), "data": {}}]}

    def update_auth_token(self, hash_token: str, session_data: Dict[str, Any]) -> None:
        """Update the authentication token and session data."""
        self._hash = hash_token
        self._session_data = session_data
        _LOGGER.debug("Alarm client auth token updated")

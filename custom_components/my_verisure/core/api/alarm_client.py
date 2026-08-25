"""Alarm client for My Verisure API."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..session_manager import SessionManager
from .alarm_command_poller import AlarmCommandPoller
from .alarm_command_response import AlarmCommandResponseInterpreter
from .alarm_command_workflow import AlarmCommandWorkflow
from .alarm_graphql_requests import AlarmGraphQLRequestPolicy
from ..application.alarm_status_service import AlarmStatusService
from .realtime_alarm_status_workflow import (
    RealtimeAlarmStatusWorkflow,
)
from ..application.models.alarm import ArmResult, DisarmResult
from .base_client import BaseClient
from .exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureError,
)
from ..log_utils import (
    redact_headers_for_log,
    redact_sensitive_data,
    should_log_detailed,
)

_LOGGER = logging.getLogger(__name__)


class AlarmClient(BaseClient):
    """Alarm client for My Verisure API."""

    def __init__(self, session_manager: SessionManager) -> None:
        """Initialize the alarm client."""
        super().__init__(session_manager=session_manager)
        self._command_poller = AlarmCommandPoller()
        self._command_response_interpreter = AlarmCommandResponseInterpreter()
        self._command_workflow = AlarmCommandWorkflow(
            interpreter=self._command_response_interpreter,
            poller=self._command_poller,
        )
        self._request_policy = AlarmGraphQLRequestPolicy()
        self._status_service = AlarmStatusService(
            Path(__file__).with_name("alarm_status.json")
        )
        self._realtime_status_workflow = RealtimeAlarmStatusWorkflow()

    def _log_graphql_outbound(
        self,
        operation: str,
        variables: dict[str, Any],
        headers: dict[str, str] | None,
    ) -> None:
        """One INFO line in production; redacted details only in developer mode."""
        _LOGGER.info("My Verisure API request: %s", operation)
        if should_log_detailed():
            _LOGGER.debug(
                "%s variables=%s headers=%s",
                operation,
                redact_sensitive_data(variables),
                redact_headers_for_log(headers),
            )

    def _log_graphql_result(self, operation: str, result: dict[str, Any]) -> None:
        """Log GraphQL JSON only in developer mode (always redacted)."""
        if should_log_detailed():
            _LOGGER.debug("%s result=%s", operation, redact_sensitive_data(result))

    async def _execute_alarm_graphql(
        self,
        operation: str,
        query: str,
        variables: Dict[str, Any],
        installation_id: str,
        panel: str,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute an alarm GraphQL operation with entry-scoped credentials."""
        try:
            headers = self._get_session_headers(session_data or {}, hash_token)
            if headers:
                headers["numinst"] = installation_id
                headers["panel"] = panel
                headers["x-capabilities"] = capabilities

            self._log_graphql_outbound(operation, variables, headers)
            result = await self._execute_query_direct(query, variables, headers)
            self._log_graphql_result(operation, result)
            return result
        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Direct alarm request failed")
            return {"errors": [{"message": "Alarm request failed", "data": {}}]}

    async def _load_alarm_status_config(self) -> dict[str, Any]:
        """Load alarm status configuration through the application service."""
        return dict(await self._status_service.load_config())

    async def _process_alarm_message(self, message: str) -> dict[str, Any]:
        """Translate an alarm message through the application service."""
        return await self._status_service.process_message(message)

    def _get_default_alarm_status(self) -> dict[str, Any]:
        """Return the default alarm status through the application service."""
        return self._status_service.default_status()


    async def get_alarm_status(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> Dict[str, Any]:
        """Get alarm status from installation services and real-time check."""
        # Get credentials from SessionManager
        hash_token, session_data = self._get_current_credentials()
        
        if not hash_token:
            raise MyVerisureAuthenticationError(
                "Not authenticated. Please login first."
            )

        try:
            try:
                service_id = "EST"

                check_alarm_result = await self._execute_check_alarm_direct(
                    installation_id,
                    panel,
                    capabilities,
                    hash_token,
                    session_data,
                )

                # Check for errors in the CheckAlarm response
                if "errors" in check_alarm_result:
                    raise MyVerisureError("Failed to get alarm status") from None

                # Check for successful response
                data = check_alarm_result.get("data", {})
                check_alarm_data = data.get("xSCheckAlarm", {})

                if not isinstance(check_alarm_data, dict) or check_alarm_data.get("res") != "OK":
                    raise MyVerisureError("Failed to get alarm status") from None

                reference_id = check_alarm_data.get("referenceId")
                if not reference_id:
                    raise MyVerisureError("Failed to get alarm status") from None

                alarm_message = await self._get_real_time_alarm_status(
                    numinst=installation_id,
                    panel=panel,
                    id_service=service_id,
                    reference_id=reference_id,
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

                if should_log_detailed():
                    _LOGGER.debug("Alarm status response received")

                # Process the alarm message and return the structured response
                if alarm_message:
                    return await self._process_alarm_message(alarm_message)
                raise MyVerisureError("Failed to get alarm status") from None

            except MyVerisureError:
                raise
            except Exception:
                raise MyVerisureError("Failed to get alarm status") from None

        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Unexpected error getting alarm status")
            raise MyVerisureError("Failed to get alarm status") from None

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
        async def transport(attempt: int) -> dict[str, Any]:
            return await self._execute_alarm_status_check_direct(
                installation_id=numinst,
                panel=panel,
                id_service=id_service,
                reference_id=reference_id,
                capabilities=capabilities,
                hash_token=hash_token,
                session_data=session_data,
            )

        return await self._realtime_status_workflow.run(transport)

    async def send_alarm_command(
        self,
        installation_id: str,
        panel: str,
        request: str,
        capabilities: str,
        current_status: str = "E",
    ) -> ArmResult:
        """Send an alarm command to the specified installation using the correct flow."""
        try:
            hash_token, session_data = self._get_current_credentials()

            async def command_transport() -> dict[str, Any]:
                return await self._execute_arm_panel_direct(
                    installation_id=installation_id,
                    panel=panel,
                    request=request,
                    current_status=current_status,
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

            def status_transport_factory(reference_id: str):
                async def status_transport(attempt: int) -> dict[str, Any]:
                    return await self._execute_arm_status_direct(
                        installation_id=installation_id,
                        panel=panel,
                        request=request,
                        reference_id=reference_id,
                        counter=attempt,
                        capabilities=capabilities,
                        hash_token=hash_token,
                        session_data=session_data,
                    )

                return status_transport

            return await self._command_workflow.arm(
                command_transport,
                status_transport_factory,
            )

        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Unexpected error sending alarm command")
            return ArmResult(success=False, message="Alarm command failed")

    async def disarm_alarm(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> DisarmResult:
        """Disarm the alarm for the specified installation using the correct flow."""
        try:
            hash_token, session_data = self._get_current_credentials()

            async def command_transport() -> dict[str, Any]:
                return await self._execute_disarm_panel_direct(
                    installation_id=installation_id,
                    panel=panel,
                    request="DARM1",
                    capabilities=capabilities,
                    hash_token=hash_token,
                    session_data=session_data,
                )

            def status_transport_factory(reference_id: str):
                async def status_transport(attempt: int) -> dict[str, Any]:
                    return await self._execute_disarm_status_direct(
                        installation_id=installation_id,
                        panel=panel,
                        request="DARM1",
                        reference_id=reference_id,
                        counter=attempt,
                        capabilities=capabilities,
                        hash_token=hash_token,
                        session_data=session_data,
                    )

                return status_transport

            return await self._command_workflow.disarm(
                command_transport,
                status_transport_factory,
            )

        except MyVerisureError:
            raise
        except Exception:
            _LOGGER.error("Unexpected error disarming alarm")
            return DisarmResult(success=False, message="Alarm disarm failed")

    async def arm_alarm_away(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> ArmResult:
        """Arm the alarm in away mode for the specified installation."""
        return await self.send_alarm_command(
            installation_id,
            panel,
            "ARM1",
            capabilities=capabilities,
        )

    async def arm_alarm_home(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> ArmResult:
        """Arm the alarm in home mode for the specified installation."""
        return await self.send_alarm_command(
            installation_id,
            panel,
            "PERI1",
            capabilities=capabilities,
        )

    async def arm_alarm_night(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> ArmResult:
        """Arm the alarm in night mode for the specified installation."""
        return await self.send_alarm_command(
            installation_id,
            panel,
            "ARMNIGHT1",
            capabilities=capabilities,
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

        request = self._request_policy.check_alarm(installation_id, panel)
        return await self._execute_alarm_graphql(
            request.operation,
            request.query,
            request.variables,
            installation_id,
            panel,
            capabilities,
            hash_token,
            session_data,
        )

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

        request = self._request_policy.check_alarm_status(
            installation_id,
            panel,
            id_service,
            reference_id,
        )
        return await self._execute_alarm_graphql(
            request.operation,
            request.query,
            request.variables,
            installation_id,
            panel,
            capabilities,
            hash_token,
            session_data,
        )

    async def _execute_arm_panel_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        capabilities: str,
        current_status: str = "E",
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute arm panel mutation using direct aiohttp request."""
        
        gql_request = self._request_policy.arm_panel(
            installation_id,
            panel,
            request,
            current_status,
        )
        return await self._execute_alarm_graphql(
            gql_request.operation,
            gql_request.query,
            gql_request.variables,
            installation_id,
            panel,
            capabilities,
            hash_token,
            session_data,
        )

    async def _execute_arm_status_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute arm status query using direct aiohttp request."""

        gql_request = self._request_policy.arm_status(
            installation_id,
            panel,
            request,
            reference_id,
            counter,
        )
        return await self._execute_alarm_graphql(
            gql_request.operation,
            gql_request.query,
            gql_request.variables,
            installation_id,
            panel,
            capabilities,
            hash_token,
            session_data,
        )

    async def _execute_disarm_panel_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute disarm panel mutation using direct aiohttp request."""

        gql_request = self._request_policy.disarm_panel(
            installation_id,
            panel,
            request,
        )
        return await self._execute_alarm_graphql(
            gql_request.operation,
            gql_request.query,
            gql_request.variables,
            installation_id,
            panel,
            capabilities,
            hash_token,
            session_data,
        )

    async def _execute_disarm_status_direct(
        self,
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
        capabilities: str,
        hash_token: Optional[str] = None,
        session_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute disarm status query using direct aiohttp request."""

        gql_request = self._request_policy.disarm_status(
            installation_id,
            panel,
            request,
            reference_id,
            counter,
        )
        return await self._execute_alarm_graphql(
            gql_request.operation,
            gql_request.query,
            gql_request.variables,
            installation_id,
            panel,
            capabilities,
            hash_token,
            session_data,
        )


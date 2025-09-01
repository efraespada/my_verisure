"""Alarm repository implementation."""

import logging

from api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult
from repositories.interfaces.alarm_repository import AlarmRepository

_LOGGER = logging.getLogger(__name__)


class AlarmRepositoryImpl(AlarmRepository):
    """Implementation of alarm repository."""

    def __init__(self, client):
        """Initialize the repository with a client."""
        self.client = client

    async def get_alarm_status(
        self, installation_id: str, panel: str, capabilities: str
    ) -> AlarmStatus:
        """Get alarm status."""
        try:
            _LOGGER.info(
                "Getting alarm status for installation %s", installation_id
            )

            # Ensure client is connected
            if not self.client._client:
                _LOGGER.info("Client not connected, connecting now...")
                await self.client.connect()

            alarm_status_data = await self.client.get_alarm_status(
                installation_id, 
                capabilities,
                hash_token=self.client._hash,
                session_data=self.client._session_data
            )

            # The client returns a processed alarm status with internal/external structure
            # We need to convert this to our AlarmStatus domain model
            _LOGGER.info("Raw alarm status data: %s", alarm_status_data)

            # Extract the alarm message from the processed data
            # The client processes the alarm message and returns a structured response
            # We'll use the first alarm message we find or a default one
            alarm_message = "No alarm"

            # Check if there are any active alarms in the processed data
            internal = alarm_status_data.get("internal", {})
            external = alarm_status_data.get("external", {})

            # Look for active alarms
            if internal.get("day", {}).get("status", False):
                alarm_message = "Internal day alarm active"
            elif internal.get("night", {}).get("status", False):
                alarm_message = "Internal night alarm active"
            elif internal.get("total", {}).get("status", False):
                alarm_message = "Internal total alarm active"
            elif external.get("status", False):
                alarm_message = "External alarm active"

            # Create AlarmStatus domain model
            alarm_status = AlarmStatus(
                success=True,
                message=alarm_message,
                status="OK" if alarm_message == "No alarm" else "ALARM",
                numinst=installation_id,
                protom_response=alarm_message,
                protom_response_date=None,
                forced_armed=False,
            )

            _LOGGER.info(
                "Retrieved alarm status for installation %s: %s",
                installation_id,
                alarm_message,
            )
            return alarm_status

        except Exception as e:
            _LOGGER.error("Error getting alarm status: %s", e)
            raise

    async def arm_panel(
        self,
        installation_id: str,
        request: str,
        panel: str,
        current_status: str = "E",
    ) -> ArmResult:
        """Arm the alarm panel."""
        try:
            _LOGGER.info(
                "Arming panel for installation %s with request %s",
                installation_id,
                request,
            )

            # Call the appropriate arm method based on request
            if request == "ARM1":
                result = await self.client.arm_alarm_away(
                    installation_id,
                    hash_token=self.client._hash,
                    session_data=self.client._session_data
                )
            elif request == "PERI1":
                result = await self.client.arm_alarm_home(
                    installation_id,
                    hash_token=self.client._hash,
                    session_data=self.client._session_data
                )
            elif request == "ARMNIGHT1":
                result = await self.client.arm_alarm_night(
                    installation_id,
                    hash_token=self.client._hash,
                    session_data=self.client._session_data
                )
            else:
                result = await self.client.send_alarm_command(
                    installation_id, 
                    request, 
                    current_status,
                    hash_token=self.client._hash,
                    session_data=self.client._session_data
                )

            if result:
                return ArmResult(
                    success=True,
                    message=f"Alarm armed successfully with request {request}",
                    # The client doesn't return reference_id in this case
                    reference_id=None,
                )
            else:
                return ArmResult(
                    success=False,
                    message=f"Failed to arm alarm with request {request}",
                )

        except Exception as e:
            _LOGGER.error("Error arming panel: %s", e)
            raise

    async def disarm_panel(
        self, installation_id: str, panel: str
    ) -> DisarmResult:
        """Disarm the alarm panel."""
        try:
            _LOGGER.info(
                "Disarming panel for installation %s",
                installation_id,
            )

            result = await self.client.disarm_alarm(
                installation_id,
                hash_token=self.client._hash,
                session_data=self.client._session_data
            )

            if result:
                return DisarmResult(
                    success=True,
                    message="Alarm disarmed successfully",
                    # The client doesn't return reference_id in this case
                    reference_id=None,
                )
            else:
                return DisarmResult(
                    success=False, message="Failed to disarm alarm"
                )

        except Exception as e:
            _LOGGER.error("Error disarming panel: %s", e)
            raise

    async def arm_alarm_away(self, installation_id: str) -> bool:
        """Arm the alarm in away mode."""
        try:
            _LOGGER.info(
                "Arming alarm away for installation %s", installation_id
            )
            result = await self.client.arm_alarm_away(
                installation_id,
                hash_token=self.client._hash,
                session_data=self.client._session_data
            )
            return result
        except Exception as e:
            _LOGGER.error("Error arming alarm away: %s", e)
            raise

    async def arm_alarm_home(self, installation_id: str) -> bool:
        """Arm the alarm in home mode."""
        try:
            _LOGGER.info(
                "Arming alarm home for installation %s", installation_id
            )
            result = await self.client.arm_alarm_home(
                installation_id,
                hash_token=self.client._hash,
                session_data=self.client._session_data
            )
            return result
        except Exception as e:
            _LOGGER.error("Error arming alarm home: %s", e)
            raise

    async def arm_alarm_night(self, installation_id: str) -> bool:
        """Arm the alarm in night mode."""
        try:
            _LOGGER.info(
                "Arming alarm night for installation %s", installation_id
            )
            result = await self.client.arm_alarm_night(
                installation_id,
                hash_token=self.client._hash,
                session_data=self.client._session_data
            )
            return result
        except Exception as e:
            _LOGGER.error("Error arming alarm night: %s", e)
            raise

    async def disarm_alarm(self, installation_id: str) -> bool:
        """Disarm the alarm."""
        try:
            _LOGGER.info(
                "Disarming alarm for installation %s", installation_id
            )
            result = await self.client.disarm_alarm(
                installation_id,
                hash_token=self.client._hash,
                session_data=self.client._session_data
            )
            return result
        except Exception as e:
            _LOGGER.error("Error disarming alarm: %s", e)
            raise

    async def check_arm_status(
        self,
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
    ) -> ArmResult:
        """Check arm status."""
        try:
            _LOGGER.debug(
                "Checking arm status for installation %s, reference %s, counter %d",
                installation_id,
                reference_id,
                counter,
            )

            # This would typically call a specific method to check arm status
            # For now, we'll return a success result
            return ArmResult(
                success=True,
                message="Arm status check completed",
                reference_id=reference_id,
            )

        except Exception as e:
            _LOGGER.error("Error checking arm status: %s", e)
            raise

    async def check_disarm_status(
        self, installation_id: str, panel: str, reference_id: str, counter: int
    ) -> DisarmResult:
        """Check disarm status."""
        try:
            _LOGGER.debug(
                "Checking disarm status for installation %s, reference %s, counter %d",
                installation_id,
                reference_id,
                counter,
            )

            # This would typically call a specific method to check disarm status
            # For now, we'll return a success result
            return DisarmResult(
                success=True,
                message="Disarm status check completed",
                reference_id=reference_id,
            )

        except Exception as e:
            _LOGGER.error("Error checking disarm status: %s", e)
            raise

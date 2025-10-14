"""Alarm repository implementation."""

import logging

from ...api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult
from ..interfaces.alarm_repository import AlarmRepository

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
            _LOGGER.warning(
                "Getting alarm status for installation %s", installation_id
            )

            # Client will manage its own session internally

            alarm_status_data = await self.client.get_alarm_status(
                installation_id, 
                panel,
                capabilities
            )

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
                data=alarm_status_data,
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
        capabilities: str,
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
                    panel,
                    capabilities=capabilities
                )
            elif request == "PERI1":
                result = await self.client.arm_alarm_home(
                    installation_id,
                    panel,
                    capabilities=capabilities
                )
            elif request == "ARMNIGHT1":
                result = await self.client.arm_alarm_night(
                    installation_id,
                    panel,
                    capabilities=capabilities
                )
            else:
                result = await self.client.send_alarm_command(
                    installation_id, 
                    panel,
                    request,
                    capabilities=capabilities,
                    current_status=current_status
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
        self, installation_id: str, panel: str, capabilities: str
    ) -> DisarmResult:
        """Disarm the alarm panel."""
        try:
            _LOGGER.info(
                "Disarming panel for installation %s",
                installation_id,
            )

            result = await self.client.disarm_alarm(
                installation_id,
                panel,
                capabilities=capabilities
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

    async def arm_alarm_away(self, installation_id: str, panel: str, capabilities: str) -> bool:
        """Arm the alarm in away mode."""
        try:
            _LOGGER.info(
                "Arming alarm away for installation %s", installation_id
            )
            result = await self.client.arm_alarm_away(
                installation_id,
                panel,
                capabilities
            )
            return result
        except Exception as e:
            _LOGGER.error("Error arming alarm away: %s", e)
            raise

    async def arm_alarm_home(self, installation_id: str, panel: str, capabilities: str) -> bool:
        """Arm the alarm in home mode."""
        try:
            _LOGGER.info(
                "Arming alarm home for installation %s", installation_id
            )
            result = await self.client.arm_alarm_home(
                installation_id,
                panel,
                capabilities
            )
            return result
        except Exception as e:
            _LOGGER.error("Error arming alarm home: %s", e)
            raise

    async def arm_alarm_night(self, installation_id: str, panel: str, capabilities: str) -> bool:
        """Arm the alarm in night mode."""
        try:
            _LOGGER.info(
                "Arming alarm night for installation %s", installation_id
            )
            result = await self.client.arm_alarm_night(
                installation_id,
                panel,
                capabilities
            )
            return result
        except Exception as e:
            _LOGGER.error("Error arming alarm night: %s", e)
            raise

    async def disarm_alarm(self, installation_id: str, panel: str, capabilities: str) -> bool:
        """Disarm the alarm."""
        try:
            _LOGGER.info(
                "Disarming alarm for installation %s", installation_id
            )
            result = await self.client.disarm_alarm(
                installation_id,
                panel,
                capabilities
            )
            return result
        except Exception as e:
            _LOGGER.error("Error disarming alarm: %s", e)
            raise

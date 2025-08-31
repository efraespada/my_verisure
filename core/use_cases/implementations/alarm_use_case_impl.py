"""Alarm use case implementation."""

import logging

from api.models.domain.alarm import AlarmStatus
from repositories.interfaces.alarm_repository import AlarmRepository
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from use_cases.interfaces.alarm_use_case import AlarmUseCase

_LOGGER = logging.getLogger(__name__)


class AlarmUseCaseImpl(AlarmUseCase):
    """Implementation of alarm use case."""

    def __init__(
        self,
        alarm_repository: AlarmRepository,
        installation_repository: InstallationRepository,
    ):
        """Initialize the use case with dependencies."""
        self.alarm_repository = alarm_repository
        self.installation_repository = installation_repository

    async def _get_installation_info(
        self, installation_id: str
    ) -> tuple[str, str]:
        """Get panel and capabilities for an installation."""
        try:
            _LOGGER.debug(
                "Getting installation info for %s from InstallationRepository",
                installation_id,
            )

            # Get installation services from InstallationRepository
            services_data = (
                await self.installation_repository.get_installation_services(
                    installation_id
                )
            )

            # Extract panel from installation data
            installation_data = services_data.installation_data or {}
            panel = installation_data.get(
                "panel", "PROTOCOL"
            )  # Fallback to default

            # Get capabilities
            capabilities = (
                services_data.capabilities or "default_capabilities"
            )  # Fallback to default

            _LOGGER.debug(
                "Installation info retrieved - Panel: %s, Capabilities: %s",
                panel,
                capabilities,
            )
            return panel, capabilities

        except Exception as e:
            _LOGGER.warning(
                "Failed to get installation info for %s, using defaults: %s",
                installation_id,
                e,
            )
            return "PROTOCOL", "default_capabilities"

    async def get_alarm_status(self, installation_id: str) -> AlarmStatus:
        """Get alarm status."""
        try:
            _LOGGER.info(
                "Getting alarm status for installation %s", installation_id
            )

            # Get panel and capabilities from installation services
            panel, capabilities = await self._get_installation_info(
                installation_id
            )

            alarm_status = await self.alarm_repository.get_alarm_status(
                installation_id, panel, capabilities
            )

            _LOGGER.info(
                "Retrieved alarm status for installation %s", installation_id
            )
            return alarm_status

        except Exception as e:
            _LOGGER.error("Error getting alarm status: %s", e)
            raise

    async def arm_away(self, installation_id: str) -> bool:
        """Arm the alarm in away mode."""
        try:
            _LOGGER.info(
                "Arming alarm in away mode for installation %s",
                installation_id,
            )

            # Get panel from installation services
            panel, _ = await self._get_installation_info(installation_id)
            current_status = "E"  # Default current status

            result = await self.alarm_repository.arm_panel(
                installation_id, "ARM1", panel, current_status
            )

            if result.success:
                _LOGGER.info("Alarm armed in away mode successfully")
            else:
                _LOGGER.error(
                    "Failed to arm alarm in away mode: %s", result.message
                )

            return result.success

        except Exception as e:
            _LOGGER.error("Error arming alarm in away mode: %s", e)
            raise

    async def arm_home(self, installation_id: str) -> bool:
        """Arm the alarm in home mode."""
        try:
            _LOGGER.info(
                "Arming alarm in home mode for installation %s",
                installation_id,
            )

            # Get panel from installation services
            panel, _ = await self._get_installation_info(installation_id)
            current_status = "E"  # Default current status

            result = await self.alarm_repository.arm_panel(
                installation_id, "PERI1", panel, current_status
            )

            if result.success:
                _LOGGER.info("Alarm armed in home mode successfully")
            else:
                _LOGGER.error(
                    "Failed to arm alarm in home mode: %s", result.message
                )

            return result.success

        except Exception as e:
            _LOGGER.error("Error arming alarm in home mode: %s", e)
            raise

    async def arm_night(self, installation_id: str) -> bool:
        """Arm the alarm in night mode."""
        try:
            _LOGGER.info(
                "Arming alarm in night mode for installation %s",
                installation_id,
            )

            # Get panel from installation services
            panel, _ = await self._get_installation_info(installation_id)
            current_status = "E"  # Default current status

            result = await self.alarm_repository.arm_panel(
                installation_id, "ARMNIGHT1", panel, current_status
            )

            if result.success:
                _LOGGER.info("Alarm armed in night mode successfully")
            else:
                _LOGGER.error(
                    "Failed to arm alarm in night mode: %s", result.message
                )

            return result.success

        except Exception as e:
            _LOGGER.error("Error arming alarm in night mode: %s", e)
            raise

    async def disarm(self, installation_id: str) -> bool:
        """Disarm the alarm."""
        try:
            _LOGGER.info(
                "Disarming alarm for installation %s", installation_id
            )

            # Get panel from installation services
            panel, _ = await self._get_installation_info(installation_id)

            result = await self.alarm_repository.disarm_panel(
                installation_id, panel
            )

            if result.success:
                _LOGGER.info("Alarm disarmed successfully")
            else:
                _LOGGER.error("Failed to disarm alarm: %s", result.message)

            return result.success

        except Exception as e:
            _LOGGER.error("Error disarming alarm: %s", e)
            raise

    # Alias methods to match test expectations
    async def arm_alarm_away(self, installation_id: str) -> bool:
        """Arm the alarm in away mode (alias for arm_away)."""
        return await self.arm_away(installation_id)

    async def arm_alarm_home(self, installation_id: str) -> bool:
        """Arm the alarm in home mode (alias for arm_home)."""
        return await self.arm_home(installation_id)

    async def arm_alarm_night(self, installation_id: str) -> bool:
        """Arm the alarm in night mode (alias for arm_night)."""
        return await self.arm_night(installation_id)

    async def disarm_alarm(self, installation_id: str) -> bool:
        """Disarm the alarm (alias for disarm)."""
        return await self.disarm(installation_id)

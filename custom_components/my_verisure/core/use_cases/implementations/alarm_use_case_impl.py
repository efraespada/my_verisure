"""Alarm use case implementation."""

import logging

from ...api.models.domain.alarm import AlarmStatus
from ...repositories.interfaces.alarm_repository import AlarmRepository
from ...repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from ..interfaces.alarm_use_case import AlarmUseCase

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
            services_data = await self.installation_repository.get_installation_services(installation_id)
            panel = services_data.installation.panel or "PROTOCOL"  # Fallback to default
            capabilities = (
                services_data.installation.capabilities or "default_capabilities"
            )  # Fallback to default

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
            panel, capabilities = await self._get_installation_info(installation_id)
            return await self.alarm_repository.get_alarm_status(
                installation_id, panel, capabilities
            )

        except Exception as e:
            _LOGGER.error("Error getting alarm status: %s", e)
            raise

    async def arm_away(self, installation_id: str, auto_arm_perimeter_with_internal: bool = False) -> bool:
        """Arm the alarm in away mode."""
        try:
            panel, capabilities = await self._get_installation_info(installation_id)
            result = await self.alarm_repository.arm_away(
                installation_id=installation_id,
                panel=panel,
                capabilities=capabilities,
                auto_arm_perimeter_with_internal=auto_arm_perimeter_with_internal,
            )

            if result.success:
                _LOGGER.warning("Alarm armed in away mode successfully")
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
            panel, capabilities = await self._get_installation_info(installation_id)
            result = await self.alarm_repository.arm_home(
                installation_id=installation_id,
                panel=panel,
                capabilities=capabilities,
            )

            if result.success:
                _LOGGER.warning("Alarm armed in home mode successfully")
            else:
                _LOGGER.error(
                    "Failed to arm alarm in home mode: %s", result.message
                )

            return result.success

        except Exception as e:
            _LOGGER.error("Error arming alarm in home mode: %s", e)
            raise

    async def arm_night(self, installation_id: str, auto_arm_perimeter_with_internal: bool = False) -> bool:
        """Arm the alarm in night mode."""
        try:
            panel, capabilities = await self._get_installation_info(installation_id)
            result = await self.alarm_repository.arm_night(
                installation_id=installation_id,
                panel=panel,
                capabilities=capabilities,
                auto_arm_perimeter_with_internal=auto_arm_perimeter_with_internal,
            )

            if result.success:
                _LOGGER.warning("Alarm armed in night mode successfully")
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
            panel, capabilities = await self._get_installation_info(installation_id)
            result = await self.alarm_repository.disarm_panel(
                installation_id, panel, capabilities
            )

            if result.success:
                _LOGGER.warning("Alarm disarmed successfully")
            else:
                _LOGGER.error("Failed to disarm alarm: %s", result.message)

            return result.success

        except Exception as e:
            _LOGGER.error("Error disarming alarm: %s", e)
            raise

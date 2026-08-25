"""Alarm use case implementation."""

import logging

from ...application.exceptions import MyVerisureError
from ...application.models.alarm import AlarmStatus, ArmResult, DisarmResult
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
            services_data = await self.installation_repository.get_installation_services(
                installation_id
            )
            panel = services_data.installation.panel
            capabilities = services_data.installation.capabilities
            if not panel or not capabilities:
                raise MyVerisureError("Installation context unavailable") from None

            return panel, capabilities

        except Exception:
            _LOGGER.warning("Failed to get installation info")
            raise MyVerisureError("Installation context unavailable") from None

    async def _resolve_panel_capabilities(
        self,
        installation_id: str,
        panel: str | None,
        capabilities: str | None,
    ) -> tuple[str, str]:
        if panel is not None and capabilities is not None:
            if (
                not isinstance(panel, str)
                or not panel.strip()
                or not isinstance(capabilities, str)
                or not capabilities.strip()
            ):
                raise MyVerisureError("Installation context unavailable")
            return panel, capabilities
        resolved_panel, resolved_capabilities = await self._get_installation_info(installation_id)
        if not resolved_panel.strip() or not resolved_capabilities.strip():
            raise MyVerisureError("Installation context unavailable")
        return resolved_panel, resolved_capabilities

    async def get_alarm_status(
        self,
        installation_id: str,
        *,
        panel: str | None = None,
        capabilities: str | None = None,
    ) -> AlarmStatus:
        """Get alarm status."""
        try:
            panel_resolved, caps_resolved = await self._resolve_panel_capabilities(
                installation_id, panel, capabilities
            )
            return await self.alarm_repository.get_alarm_status(
                installation_id, panel_resolved, caps_resolved
            )

        except Exception:
            _LOGGER.error("Error getting alarm status")
            raise

    async def arm_away(
        self,
        installation_id: str,
        auto_arm_perimeter_with_internal: bool = False,
        *,
        panel: str | None = None,
        capabilities: str | None = None,
    ) -> ArmResult:
        """Arm the alarm in away mode."""
        try:
            panel_resolved, caps_resolved = await self._resolve_panel_capabilities(
                installation_id, panel, capabilities
            )
            result = await self.alarm_repository.arm_away(
                installation_id=installation_id,
                panel=panel_resolved,
                capabilities=caps_resolved,
                auto_arm_perimeter_with_internal=auto_arm_perimeter_with_internal,
            )

            if result.success:
                _LOGGER.warning("Alarm armed in away mode successfully")
            else:
                _LOGGER.error("Failed to arm alarm in away mode")

            return result

        except Exception:
            _LOGGER.error("Error arming alarm in away mode")
            raise

    async def arm_home(
        self,
        installation_id: str,
        *,
        panel: str | None = None,
        capabilities: str | None = None,
    ) -> ArmResult:
        """Arm the alarm in home mode."""
        try:
            panel_resolved, caps_resolved = await self._resolve_panel_capabilities(
                installation_id, panel, capabilities
            )
            result = await self.alarm_repository.arm_home(
                installation_id=installation_id,
                panel=panel_resolved,
                capabilities=caps_resolved,
            )

            if result.success:
                _LOGGER.warning("Alarm armed in home mode successfully")
            else:
                _LOGGER.error("Failed to arm alarm in home mode")

            return result

        except Exception:
            _LOGGER.error("Error arming alarm in home mode")
            raise

    async def arm_night(
        self,
        installation_id: str,
        auto_arm_perimeter_with_internal: bool = False,
        *,
        panel: str | None = None,
        capabilities: str | None = None,
    ) -> ArmResult:
        """Arm the alarm in night mode."""
        try:
            panel_resolved, caps_resolved = await self._resolve_panel_capabilities(
                installation_id, panel, capabilities
            )
            result = await self.alarm_repository.arm_night(
                installation_id=installation_id,
                panel=panel_resolved,
                capabilities=caps_resolved,
                auto_arm_perimeter_with_internal=auto_arm_perimeter_with_internal,
            )

            if result.success:
                _LOGGER.warning("Alarm armed in night mode successfully")
            else:
                _LOGGER.error("Failed to arm alarm in night mode")

            return result

        except Exception:
            _LOGGER.error("Error arming alarm in night mode")
            raise

    async def disarm(
        self,
        installation_id: str,
        *,
        panel: str | None = None,
        capabilities: str | None = None,
    ) -> DisarmResult:
        """Disarm the alarm."""
        try:
            panel_resolved, caps_resolved = await self._resolve_panel_capabilities(
                installation_id, panel, capabilities
            )
            result = await self.alarm_repository.disarm_panel(
                installation_id, panel_resolved, caps_resolved
            )

            if result.success:
                _LOGGER.warning("Alarm disarmed successfully")
            else:
                _LOGGER.error("Failed to disarm alarm")

            return result

        except Exception:
            _LOGGER.error("Error disarming alarm")
            raise

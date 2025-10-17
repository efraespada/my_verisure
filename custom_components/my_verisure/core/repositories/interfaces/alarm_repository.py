"""Alarm repository interface."""

from abc import ABC, abstractmethod

from ...api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult


class AlarmRepository(ABC):
    """Interface for alarm repository."""

    @abstractmethod
    async def get_alarm_status(
        self, installation_id: str, panel: str, capabilities: str
    ) -> AlarmStatus:
        """Get alarm status."""
        pass

    @abstractmethod
    async def arm_panel(
        self,
        installation_id: str,
        request: str,
        panel: str,
        capabilities: str,
        current_status: str = "E",
    ) -> ArmResult:
        """Arm the alarm panel."""
        pass

    @abstractmethod
    async def disarm_panel(
        self, installation_id: str, panel: str, capabilities: str
    ) -> DisarmResult:
        """Disarm the alarm panel."""
        pass

    @abstractmethod
    async def arm_home(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
    ) -> ArmResult:
        """Arm the alarm panel in home mode."""
        pass

    @abstractmethod
    async def arm_away(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
        auto_arm_perimeter_with_internal: bool = False,
    ) -> ArmResult:
        """Arm the alarm panel in away mode."""
        pass

    @abstractmethod
    async def arm_night(
        self,
        installation_id: str,
        panel: str,
        capabilities: str,
        auto_arm_perimeter_with_internal: bool = False,
    ) -> ArmResult:
        """Arm the alarm panel in night mode."""
        pass

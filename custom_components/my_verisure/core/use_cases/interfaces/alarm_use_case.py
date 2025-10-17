"""Alarm use case interface."""

from abc import ABC, abstractmethod

from ...api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult


class AlarmUseCase(ABC):
    """Interface for alarm use case."""

    @abstractmethod
    async def get_alarm_status(self, installation_id: str) -> AlarmStatus:
        """Get alarm status."""
        pass

    @abstractmethod
    async def arm_away(self, installation_id: str, auto_arm_perimeter_with_internal: bool = False) -> ArmResult:
        """Arm the alarm in away mode."""
        pass

    @abstractmethod
    async def arm_home(self, installation_id: str) -> ArmResult:
        """Arm the alarm in home mode."""
        pass

    @abstractmethod
    async def arm_night(self, installation_id: str, auto_arm_perimeter_with_internal: bool = False) -> ArmResult:
        """Arm the alarm in night mode."""
        pass

    @abstractmethod
    async def disarm(self, installation_id: str) -> DisarmResult:
        """Disarm the alarm."""
        pass

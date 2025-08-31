"""Alarm repository interface."""

from abc import ABC, abstractmethod

from api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult


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
        current_status: str = "E",
    ) -> ArmResult:
        """Arm the alarm panel."""
        pass

    @abstractmethod
    async def disarm_panel(
        self, installation_id: str, panel: str
    ) -> DisarmResult:
        """Disarm the alarm panel."""
        pass

    @abstractmethod
    async def check_arm_status(
        self,
        installation_id: str,
        panel: str,
        request: str,
        reference_id: str,
        counter: int,
    ) -> ArmResult:
        """Check arm status."""
        pass

    @abstractmethod
    async def check_disarm_status(
        self, installation_id: str, panel: str, reference_id: str, counter: int
    ) -> DisarmResult:
        """Check disarm status."""
        pass

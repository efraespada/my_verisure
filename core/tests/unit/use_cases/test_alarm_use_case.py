#!/usr/bin/env python3
"""
Unit tests for AlarmUseCase implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

# Add the package root to the path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl
from use_cases.interfaces.alarm_use_case import AlarmUseCase
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from repositories.interfaces.alarm_repository import AlarmRepository
from api.models.domain.alarm import AlarmStatus
from api.models.domain.installation import InstallationServices
from api.exceptions import MyVerisureError


class TestAlarmUseCase:
    """Test cases for AlarmUseCase implementation."""

    @pytest.fixture
    def mock_alarm_repository(self):
        """Create a mock alarm repository."""
        mock_repo = Mock(spec=AlarmRepository)
        mock_repo.get_alarm_status = AsyncMock()
        mock_repo.arm_alarm_away = AsyncMock()
        mock_repo.arm_alarm_home = AsyncMock()
        mock_repo.arm_alarm_night = AsyncMock()
        mock_repo.disarm_alarm = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_installation_repository(self):
        """Create a mock installation repository."""
        mock_repo = Mock(spec=InstallationRepository)
        mock_repo.get_installation_services = AsyncMock()

        # Default mock response for installation services
        mock_services = InstallationServices(
            success=True,
            message="Success",
            installation_data={"panel": "PROTOCOL"},
            capabilities="default_capabilities",
        )
        mock_repo.get_installation_services.return_value = mock_services

        return mock_repo

    @pytest.fixture
    def alarm_use_case(
        self, mock_alarm_repository, mock_installation_repository
    ):
        """Create AlarmUseCase instance with mocked dependencies."""
        return AlarmUseCaseImpl(
            alarm_repository=mock_alarm_repository,
            installation_repository=mock_installation_repository,
        )

    def test_alarm_use_case_implements_interface(self, alarm_use_case):
        """Test that AlarmUseCaseImpl implements AlarmUseCase interface."""
        assert isinstance(alarm_use_case, AlarmUseCase)

    @pytest.mark.asyncio
    async def test_get_alarm_status_success(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test successful get alarm status."""
        # Arrange
        installation_id = "12345"
        expected_status = AlarmStatus(
            success=True,
            message="Alarm status retrieved successfully",
            status="ARMED",
            numinst=installation_id,
        )

        mock_alarm_repository.get_alarm_status.return_value = expected_status

        # Act
        result = await alarm_use_case.get_alarm_status(installation_id)

        # Assert
        assert result.success is True
        assert result.message == "Alarm status retrieved successfully"
        assert result.status == "ARMED"
        assert result.numinst == installation_id
        mock_alarm_repository.get_alarm_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_alarm_status_raises_exception(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test get alarm status raises exception."""
        # Arrange
        installation_id = "12345"
        mock_alarm_repository.get_alarm_status.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_use_case.get_alarm_status(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_away_success(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test successful arm alarm away."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=True
        mock_result = Mock()
        mock_result.success = True
        mock_alarm_repository.arm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.arm_alarm_away(installation_id)

        # Assert
        assert result is True
        mock_alarm_repository.arm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_alarm_away_failure(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test failed arm alarm away."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=False
        mock_result = Mock()
        mock_result.success = False
        mock_alarm_repository.arm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.arm_alarm_away(installation_id)

        # Assert
        assert result is False
        mock_alarm_repository.arm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_alarm_home_success(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test successful arm alarm home."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=True
        mock_result = Mock()
        mock_result.success = True
        mock_alarm_repository.arm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.arm_alarm_home(installation_id)

        # Assert
        assert result is True
        mock_alarm_repository.arm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_alarm_home_failure(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test failed arm alarm home."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=False
        mock_result = Mock()
        mock_result.success = False
        mock_alarm_repository.arm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.arm_alarm_home(installation_id)

        # Assert
        assert result is False
        mock_alarm_repository.arm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_alarm_night_success(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test successful arm alarm night."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=True
        mock_result = Mock()
        mock_result.success = True
        mock_alarm_repository.arm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.arm_alarm_night(installation_id)

        # Assert
        assert result is True
        mock_alarm_repository.arm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_alarm_night_failure(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test failed arm alarm night."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=False
        mock_result = Mock()
        mock_result.success = False
        mock_alarm_repository.arm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.arm_alarm_night(installation_id)

        # Assert
        assert result is False
        mock_alarm_repository.arm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_disarm_alarm_success(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test successful disarm alarm."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=True
        mock_result = Mock()
        mock_result.success = True
        mock_alarm_repository.disarm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.disarm_alarm(installation_id)

        # Assert
        assert result is True
        mock_alarm_repository.disarm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_disarm_alarm_failure(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test failed disarm alarm."""
        # Arrange
        installation_id = "12345"
        # Configure the mock to return a mock object with success=False
        mock_result = Mock()
        mock_result.success = False
        mock_alarm_repository.disarm_panel.return_value = mock_result

        # Act
        result = await alarm_use_case.disarm_alarm(installation_id)

        # Assert
        assert result is False
        mock_alarm_repository.disarm_panel.assert_called_once()

    @pytest.mark.asyncio
    async def test_arm_alarm_away_raises_exception(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test arm alarm away raises exception."""
        # Arrange
        installation_id = "12345"
        mock_alarm_repository.arm_panel.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_use_case.arm_alarm_away(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_home_raises_exception(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test arm alarm home raises exception."""
        # Arrange
        installation_id = "12345"
        mock_alarm_repository.arm_panel.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_use_case.arm_alarm_home(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_night_raises_exception(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test arm alarm night raises exception."""
        # Arrange
        installation_id = "12345"
        mock_alarm_repository.arm_panel.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_use_case.arm_alarm_night(installation_id)

    @pytest.mark.asyncio
    async def test_disarm_alarm_raises_exception(
        self, alarm_use_case, mock_alarm_repository
    ):
        """Test disarm alarm raises exception."""
        # Arrange
        installation_id = "12345"
        mock_alarm_repository.disarm_panel.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_use_case.disarm_alarm(installation_id)


if __name__ == "__main__":
    pytest.main([__file__])

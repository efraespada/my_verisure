#!/usr/bin/env python3
"""
Unit tests for AlarmRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

# Add the package root to the path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from repositories.implementations.alarm_repository_impl import (
    AlarmRepositoryImpl,
)
from repositories.interfaces.alarm_repository import AlarmRepository
from api.exceptions import MyVerisureError


class TestAlarmRepository:
    """Test cases for AlarmRepository implementation."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MyVerisureClient."""
        mock_client = Mock()
        mock_client.get_alarm_status = AsyncMock()
        mock_client.arm_alarm_away = AsyncMock()
        mock_client.arm_alarm_home = AsyncMock()
        mock_client.arm_alarm_night = AsyncMock()
        mock_client.disarm_alarm = AsyncMock()
        return mock_client

    @pytest.fixture
    def alarm_repository(self, mock_client):
        """Create AlarmRepository instance with mocked client."""
        return AlarmRepositoryImpl(client=mock_client)

    def test_alarm_repository_implements_interface(self, alarm_repository):
        """Test that AlarmRepositoryImpl implements AlarmRepository interface."""
        assert isinstance(alarm_repository, AlarmRepository)

    @pytest.mark.asyncio
    async def test_get_alarm_status_success(
        self, alarm_repository, mock_client
    ):
        """Test successful get alarm status."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        capabilities = "test_capabilities"
        expected_status_data = {
            "internal": {
                "day": {"status": True},
                "night": {"status": False},
                "total": {"status": True},
            },
            "external": {"status": False},
        }

        mock_client.get_alarm_status.return_value = expected_status_data

        # Act
        result = await alarm_repository.get_alarm_status(
            installation_id, panel, capabilities
        )

        # Assert
        assert result is not None
        mock_client.get_alarm_status.assert_called_once_with(
            installation_id, capabilities
        )

    @pytest.mark.asyncio
    async def test_get_alarm_status_raises_exception(
        self, alarm_repository, mock_client
    ):
        """Test get alarm status raises exception."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        capabilities = "test_capabilities"
        mock_client.get_alarm_status.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_repository.get_alarm_status(
                installation_id, panel, capabilities
            )

    @pytest.mark.asyncio
    async def test_arm_alarm_away_success(self, alarm_repository, mock_client):
        """Test successful arm alarm away."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_away.return_value = True

        # Act
        result = await alarm_repository.arm_alarm_away(installation_id)

        # Assert
        assert result is True
        mock_client.arm_alarm_away.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_away_failure(self, alarm_repository, mock_client):
        """Test failed arm alarm away."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_away.return_value = False

        # Act
        result = await alarm_repository.arm_alarm_away(installation_id)

        # Assert
        assert result is False
        mock_client.arm_alarm_away.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_home_success(self, alarm_repository, mock_client):
        """Test successful arm alarm home."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_home.return_value = True

        # Act
        result = await alarm_repository.arm_alarm_home(installation_id)

        # Assert
        assert result is True
        mock_client.arm_alarm_home.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_home_failure(self, alarm_repository, mock_client):
        """Test failed arm alarm home."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_home.return_value = False

        # Act
        result = await alarm_repository.arm_alarm_home(installation_id)

        # Assert
        assert result is False
        mock_client.arm_alarm_home.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_night_success(
        self, alarm_repository, mock_client
    ):
        """Test successful arm alarm night."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_night.return_value = True

        # Act
        result = await alarm_repository.arm_alarm_night(installation_id)

        # Assert
        assert result is True
        mock_client.arm_alarm_night.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_night_failure(
        self, alarm_repository, mock_client
    ):
        """Test failed arm alarm night."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_night.return_value = False

        # Act
        result = await alarm_repository.arm_alarm_night(installation_id)

        # Assert
        assert result is False
        mock_client.arm_alarm_night.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_disarm_alarm_success(self, alarm_repository, mock_client):
        """Test successful disarm alarm."""
        # Arrange
        installation_id = "12345"
        mock_client.disarm_alarm.return_value = True

        # Act
        result = await alarm_repository.disarm_alarm(installation_id)

        # Assert
        assert result is True
        mock_client.disarm_alarm.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_disarm_alarm_failure(self, alarm_repository, mock_client):
        """Test failed disarm alarm."""
        # Arrange
        installation_id = "12345"
        mock_client.disarm_alarm.return_value = False

        # Act
        result = await alarm_repository.disarm_alarm(installation_id)

        # Assert
        assert result is False
        mock_client.disarm_alarm.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_away_raises_exception(
        self, alarm_repository, mock_client
    ):
        """Test arm alarm away raises exception."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_away.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_repository.arm_alarm_away(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_home_raises_exception(
        self, alarm_repository, mock_client
    ):
        """Test arm alarm home raises exception."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_home.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_repository.arm_alarm_home(installation_id)

    @pytest.mark.asyncio
    async def test_arm_alarm_night_raises_exception(
        self, alarm_repository, mock_client
    ):
        """Test arm alarm night raises exception."""
        # Arrange
        installation_id = "12345"
        mock_client.arm_alarm_night.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_repository.arm_alarm_night(installation_id)

    @pytest.mark.asyncio
    async def test_disarm_alarm_raises_exception(
        self, alarm_repository, mock_client
    ):
        """Test disarm alarm raises exception."""
        # Arrange
        installation_id = "12345"
        mock_client.disarm_alarm.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await alarm_repository.disarm_alarm(installation_id)


if __name__ == "__main__":
    pytest.main([__file__])

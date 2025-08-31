#!/usr/bin/env python3
"""
Unit tests for AuthRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

# Add the package root to the path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from repositories.implementations.auth_repository_impl import (
    AuthRepositoryImpl,
)
from repositories.interfaces.auth_repository import AuthRepository
from api.models.domain.auth import Auth
from api.models.domain.session import DeviceIdentifiers
from api.exceptions import MyVerisureAuthenticationError, MyVerisureOTPError


class TestAuthRepository:
    """Test cases for AuthRepository implementation."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MyVerisureClient."""
        mock_client = Mock()
        mock_client.login = AsyncMock()
        mock_client.send_otp = AsyncMock()
        mock_client.verify_otp = AsyncMock()
        mock_client.get_available_phones = Mock()
        return mock_client

    @pytest.fixture
    def auth_repository(self, mock_client):
        """Create AuthRepository instance with mocked client."""
        return AuthRepositoryImpl(client=mock_client)

    def test_auth_repository_implements_interface(self, auth_repository):
        """Test that AuthRepositoryImpl implements AuthRepository interface."""
        assert isinstance(auth_repository, AuthRepository)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_repository, mock_client):
        """Test successful login."""
        # Arrange
        auth = Auth(username="test_user", password="test_password")
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="",
            device_resolution="",
            generated_time=0,
        )

        mock_client.login.return_value = True
        # Mock the client's internal state after successful login
        mock_client._hash = "test_hash"
        mock_client._session_data = {"user": "test_user", "lang": "es"}

        # Act
        result = await auth_repository.login(auth, device_identifiers)

        # Assert
        assert result.success is True
        assert result.hash == "test_hash"
        assert result.message == "Login successful"
        mock_client.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_failure(self, auth_repository, mock_client):
        """Test failed login."""
        # Arrange
        auth = Auth(username="test_user", password="wrong_password")
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="",
            device_resolution="",
            generated_time=0,
        )
        mock_client.login.side_effect = MyVerisureAuthenticationError(
            "Invalid credentials"
        )

        # Act
        result = await auth_repository.login(auth, device_identifiers)

        # Assert
        assert result.success is False
        assert result.hash is None
        assert "Invalid credentials" in result.message
        mock_client.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_otp_required(self, auth_repository, mock_client):
        """Test login requires OTP."""
        # Arrange
        auth = Auth(username="test_user", password="test_password")
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="",
            device_resolution="",
            generated_time=0,
        )
        mock_client.login.side_effect = MyVerisureOTPError("OTP required")

        # Act
        result = await auth_repository.login(auth, device_identifiers)

        # Assert
        assert result.success is False
        assert result.hash is None
        assert "OTP required" in result.message
        mock_client.login.assert_called_once()

    def test_get_available_phones_success(self, auth_repository, mock_client):
        """Test getting available phones."""
        # Arrange
        expected_phones = [
            {"id": 1, "phone": "+34600000001"},
            {"id": 2, "phone": "+34600000002"},
        ]
        mock_client.get_available_phones.return_value = expected_phones

        # Act
        phones = auth_repository.get_available_phones()

        # Assert
        assert phones == expected_phones
        mock_client.get_available_phones.assert_called_once()

    def test_get_available_phones_empty(self, auth_repository, mock_client):
        """Test getting available phones returns empty list."""
        # Arrange
        mock_client.get_available_phones.return_value = []

        # Act
        phones = auth_repository.get_available_phones()

        # Assert
        assert phones == []
        mock_client.get_available_phones.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_otp_success(self, auth_repository, mock_client):
        """Test successful OTP send."""
        # Arrange
        record_id = 1
        otp_hash = "test_hash"
        mock_client.send_otp.return_value = True

        # Act
        result = await auth_repository.send_otp(record_id, otp_hash)

        # Assert
        assert result is True
        mock_client.send_otp.assert_called_once_with(record_id, otp_hash)

    @pytest.mark.asyncio
    async def test_send_otp_failure(self, auth_repository, mock_client):
        """Test failed OTP send."""
        # Arrange
        record_id = 1
        otp_hash = "test_hash"
        mock_client.send_otp.return_value = False

        # Act
        result = await auth_repository.send_otp(record_id, otp_hash)

        # Assert
        assert result is False
        mock_client.send_otp.assert_called_once_with(record_id, otp_hash)

    @pytest.mark.asyncio
    async def test_send_otp_raises_exception(
        self, auth_repository, mock_client
    ):
        """Test OTP send raises exception."""
        # Arrange
        record_id = 1
        otp_hash = "test_hash"
        mock_client.send_otp.side_effect = MyVerisureOTPError(
            "Failed to send OTP"
        )

        # Act & Assert
        with pytest.raises(MyVerisureOTPError, match="Failed to send OTP"):
            await auth_repository.send_otp(record_id, otp_hash)

    @pytest.mark.asyncio
    async def test_verify_otp_success(self, auth_repository, mock_client):
        """Test successful OTP verification."""
        # Arrange
        otp_code = "123456"
        otp_hash = "test_hash"
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="",
            device_resolution="",
            generated_time=0,
        )
        mock_client.verify_otp.return_value = True
        mock_client._hash = "test_hash"
        mock_client._refresh_token = "refresh_token"
        mock_client._session_data = {
            "lang": "es",
            "legals": False,
            "changePassword": False,
            "needDeviceAuthorization": False,
        }

        # Act
        result = await auth_repository.verify_otp(
            otp_code, otp_hash, device_identifiers
        )

        # Assert
        assert result.success is True
        assert result.message == "OTP verification successful"
        assert result.hash == "test_hash"
        # The client's verify_otp method only takes otp_code, not the other parameters
        mock_client.verify_otp.assert_called_once_with(otp_code)

    @pytest.mark.asyncio
    async def test_verify_otp_failure(self, auth_repository, mock_client):
        """Test failed OTP verification."""
        # Arrange
        otp_code = "123456"
        otp_hash = "test_hash"
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="",
            device_resolution="",
            generated_time=0,
        )
        mock_client.verify_otp.return_value = False

        # Act
        result = await auth_repository.verify_otp(
            otp_code, otp_hash, device_identifiers
        )

        # Assert
        assert result.success is False
        assert result.message == "OTP verification failed"
        # The client's verify_otp method only takes otp_code, not the other parameters
        mock_client.verify_otp.assert_called_once_with(otp_code)

    @pytest.mark.asyncio
    async def test_verify_otp_raises_exception(
        self, auth_repository, mock_client
    ):
        """Test OTP verification raises exception."""
        # Arrange
        otp_code = "123456"
        otp_hash = "test_hash"
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="",
            device_resolution="",
            generated_time=0,
        )
        mock_client.verify_otp.side_effect = MyVerisureOTPError("Invalid OTP")

        # Act & Assert
        with pytest.raises(MyVerisureOTPError, match="Invalid OTP"):
            await auth_repository.verify_otp(
                otp_code, otp_hash, device_identifiers
            )


if __name__ == "__main__":
    pytest.main([__file__])

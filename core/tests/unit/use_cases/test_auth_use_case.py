#!/usr/bin/env python3
"""
Unit tests for AuthUseCase implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

# Add the package root to the path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from use_cases.interfaces.auth_use_case import AuthUseCase
from repositories.interfaces.auth_repository import AuthRepository
from api.models.domain.auth import Auth, AuthResult
from api.models.domain.session import DeviceIdentifiers
from api.exceptions import MyVerisureAuthenticationError, MyVerisureOTPError


class TestAuthUseCase:
    """Test cases for AuthUseCase implementation."""

    @pytest.fixture
    def mock_auth_repository(self):
        """Create a mock auth repository."""
        mock_repo = Mock(spec=AuthRepository)
        mock_repo.login = AsyncMock()
        mock_repo.send_otp = AsyncMock()
        mock_repo.verify_otp = AsyncMock()
        mock_repo.get_available_phones = Mock()
        return mock_repo

    @pytest.fixture
    def auth_use_case(self, mock_auth_repository):
        """Create AuthUseCase instance with mocked dependencies."""
        return AuthUseCaseImpl(auth_repository=mock_auth_repository)

    def test_auth_use_case_implements_interface(self, auth_use_case):
        """Test that AuthUseCaseImpl implements AuthUseCase interface."""
        assert isinstance(auth_use_case, AuthUseCase)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_use_case, mock_auth_repository):
        """Test successful login."""
        # Arrange
        username = "test_user"
        password = "test_password"
        expected_auth = Auth(username=username, password=password)

        expected_result = AuthResult(
            success=True, hash="test_hash", message="Login successful"
        )

        mock_auth_repository.login.return_value = expected_result

        # Act
        result = await auth_use_case.login(username, password)

        # Assert
        assert result.success is True
        assert result.hash == "test_hash"
        assert result.message == "Login successful"
        # Verify the call was made with both auth and device identifiers
        mock_auth_repository.login.assert_called_once()
        call_args = mock_auth_repository.login.call_args[0]
        assert len(call_args) == 2
        assert call_args[0] == expected_auth
        assert isinstance(call_args[1], DeviceIdentifiers)

    @pytest.mark.asyncio
    async def test_login_failure(self, auth_use_case, mock_auth_repository):
        """Test failed login."""
        # Arrange
        username = "test_user"
        password = "wrong_password"
        expected_auth = Auth(username=username, password=password)
        expected_result = AuthResult(
            success=False, hash=None, message="Invalid credentials"
        )

        mock_auth_repository.login.return_value = expected_result

        # Act
        result = await auth_use_case.login(username, password)

        # Assert
        assert result.success is False
        assert result.hash is None
        assert result.message == "Invalid credentials"
        # Verify the call was made with both auth and device identifiers
        mock_auth_repository.login.assert_called_once()
        call_args = mock_auth_repository.login.call_args[0]
        assert len(call_args) == 2
        assert call_args[0] == expected_auth
        assert isinstance(call_args[1], DeviceIdentifiers)

    @pytest.mark.asyncio
    async def test_login_raises_exception(
        self, auth_use_case, mock_auth_repository
    ):
        """Test login raises exception."""
        # Arrange
        username = "test_user"
        password = "test_password"
        mock_auth_repository.login.side_effect = MyVerisureAuthenticationError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(
            MyVerisureAuthenticationError, match="Connection failed"
        ):
            await auth_use_case.login(username, password)

    def test_get_available_phones(self, auth_use_case, mock_auth_repository):
        """Test getting available phones."""
        # Arrange
        expected_phones = [
            {"id": 1, "phone": "+34600000001"},
            {"id": 2, "phone": "+34600000002"},
        ]

        # Mock the OTP data in the use case
        from api.exceptions import MyVerisureOTPError
        from api.models.dto.auth_dto import PhoneDTO

        # Create mock OTP exception with phone data
        mock_otp_exception = MyVerisureOTPError("OTP required")
        mock_otp_exception.phones = [
            PhoneDTO(id=1, phone="+34600000001"),
            PhoneDTO(id=2, phone="+34600000002"),
        ]
        mock_otp_exception.otp_hash = "test_hash"

        auth_use_case._otp_data = mock_otp_exception

        # Act
        phones = auth_use_case.get_available_phones()

        # Assert
        assert phones == expected_phones
        # Note: get_available_phones doesn't call the repository, it uses internal state

    @pytest.mark.asyncio
    async def test_send_otp_success(self, auth_use_case, mock_auth_repository):
        """Test successful OTP send."""
        # Arrange
        record_id = 1
        otp_hash = "test_hash"
        mock_auth_repository.send_otp.return_value = True

        # Act
        result = await auth_use_case.send_otp(record_id, otp_hash)

        # Assert
        assert result is True
        mock_auth_repository.send_otp.assert_called_once_with(
            record_id, otp_hash
        )

    @pytest.mark.asyncio
    async def test_send_otp_failure(self, auth_use_case, mock_auth_repository):
        """Test failed OTP send."""
        # Arrange
        record_id = 1
        otp_hash = "test_hash"
        mock_auth_repository.send_otp.return_value = False

        # Act
        result = await auth_use_case.send_otp(record_id, otp_hash)

        # Assert
        assert result is False
        mock_auth_repository.send_otp.assert_called_once_with(
            record_id, otp_hash
        )

    @pytest.mark.asyncio
    async def test_verify_otp_success(
        self, auth_use_case, mock_auth_repository
    ):
        """Test successful OTP verification."""
        # Arrange
        otp_code = "123456"
        mock_auth_repository.verify_otp.return_value = AuthResult(
            success=True,
            message="OTP verification successful",
            hash="test_hash",
        )

        # Mock the OTP data in the use case
        from api.exceptions import MyVerisureOTPError

        mock_otp_exception = MyVerisureOTPError("OTP required")
        mock_otp_exception.otp_hash = "test_hash"
        auth_use_case._otp_data = mock_otp_exception

        # Act
        result = await auth_use_case.verify_otp(otp_code)

        # Assert
        assert result is True
        mock_auth_repository.verify_otp.assert_called_once()
        call_args = mock_auth_repository.verify_otp.call_args[0]
        assert call_args[0] == otp_code
        assert call_args[1] == "test_hash"
        assert isinstance(call_args[2], DeviceIdentifiers)

    @pytest.mark.asyncio
    async def test_verify_otp_failure(
        self, auth_use_case, mock_auth_repository
    ):
        """Test failed OTP verification."""
        # Arrange
        otp_code = "123456"
        mock_auth_repository.verify_otp.return_value = AuthResult(
            success=False, message="OTP verification failed"
        )

        # Mock the OTP data in the use case
        from api.exceptions import MyVerisureOTPError

        mock_otp_exception = MyVerisureOTPError("OTP required")
        mock_otp_exception.otp_hash = "test_hash"
        auth_use_case._otp_data = mock_otp_exception

        # Act
        result = await auth_use_case.verify_otp(otp_code)

        # Assert
        assert result is False
        mock_auth_repository.verify_otp.assert_called_once()
        call_args = mock_auth_repository.verify_otp.call_args[0]
        assert call_args[0] == otp_code
        assert call_args[1] == "test_hash"
        assert isinstance(call_args[2], DeviceIdentifiers)

    @pytest.mark.asyncio
    async def test_verify_otp_raises_exception(
        self, auth_use_case, mock_auth_repository
    ):
        """Test OTP verification raises exception."""
        # Arrange
        otp_code = "123456"
        mock_auth_repository.verify_otp.side_effect = MyVerisureOTPError(
            "Invalid OTP"
        )

        # Mock the OTP data in the use case
        mock_otp_exception = MyVerisureOTPError("OTP required")
        mock_otp_exception.otp_hash = "test_hash"
        auth_use_case._otp_data = mock_otp_exception

        # Act & Assert
        with pytest.raises(MyVerisureOTPError, match="Invalid OTP"):
            await auth_use_case.verify_otp(otp_code)


if __name__ == "__main__":
    pytest.main([__file__])

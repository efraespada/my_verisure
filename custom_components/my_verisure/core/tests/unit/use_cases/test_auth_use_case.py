#!/usr/bin/env python3
"""
Unit tests for AuthUseCase implementation.
"""

import time

import pytest
from unittest.mock import Mock, AsyncMock

from ....use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from ....use_cases.interfaces.auth_use_case import AuthUseCase
from ....repositories.interfaces.auth_repository import AuthRepository
from ....application.models.auth import Auth, AuthResult, OTPData, Phone
from ....api.exceptions import (
    MyVerisureAuthenticationError,
    MyVerisureConnectionError,
    MyVerisureDeviceAuthorizationError,
    MyVerisureOTPError,
    MyVerisurePersistenceError,
)


class TestAuthUseCase:
    """Test cases for AuthUseCase implementation."""

    @pytest.fixture
    def mock_auth_repository(self):
        """Create a mock auth repository."""
        mock_repo = Mock(spec=AuthRepository)
        mock_repo.login = AsyncMock()
        mock_repo.send_otp = AsyncMock()
        mock_repo.verify_otp = AsyncMock()
        mock_repo.invalidate_otp_challenge = Mock()
        mock_repo.get_available_phones = Mock()
        return mock_repo

    @pytest.fixture
    def auth_use_case(self, mock_auth_repository):
        """Create AuthUseCase instance with mocked dependencies."""
        session_persistence = Mock()
        session_persistence.persist_result = AsyncMock()
        value = AuthUseCaseImpl(
            auth_repository=mock_auth_repository,
            session_persistence=session_persistence,
        )
        value._otp_expires_at = time.monotonic() + 300
        return value

    def test_auth_use_case_implements_interface(self, auth_use_case):
        """Test that AuthUseCaseImpl implements AuthUseCase interface."""
        assert isinstance(auth_use_case, AuthUseCase)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_use_case, mock_auth_repository):
        """Test successful login."""
        # Arrange
        username = "USER_SENTINEL"
        password = "PASSWORD_SENTINEL"
        expected_auth = Auth(username=username, password=password)

        expected_result = AuthResult(
            success=True, hash="HASH_SENTINEL", message="Login successful"
        )

        mock_auth_repository.login.return_value = expected_result

        # Act
        result = await auth_use_case.login(username, password)

        # Assert
        assert result.success is True
        assert result.hash == "HASH_SENTINEL"
        assert result.message == "Login successful"
        # Verify the call was made with both auth and device identifiers
        mock_auth_repository.login.assert_called_once()
        call_args = mock_auth_repository.login.call_args[0]
        assert len(call_args) == 1
        assert call_args[0] == expected_auth

    @pytest.mark.asyncio
    async def test_login_failure(self, auth_use_case, mock_auth_repository):
        """Test failed login."""
        # Arrange
        username = "USER_SENTINEL"
        password = "PASSWORD_SENTINEL"
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
        assert len(call_args) == 1
        assert call_args[0] == expected_auth

    @pytest.mark.asyncio
    async def test_login_invalidates_previous_otp_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="OLD_HASH")
        auth_use_case._otp_expires_at = time.monotonic() + 300
        mock_auth_repository.login.return_value = AuthResult(
            success=False, message="login failed"
        )

        result = await auth_use_case.login("USER", "PASSWORD")

        assert result.success is False
        assert auth_use_case._otp_data is None
        assert auth_use_case._otp_expires_at is None
        assert auth_use_case._otp_attempts == 0
        with pytest.raises(MyVerisureOTPError, match="No active OTP challenge"):
            await auth_use_case.verify_otp("123456")

    @pytest.mark.asyncio
    async def test_login_raises_exception(
        self, auth_use_case, mock_auth_repository
    ):
        """Test login raises exception."""
        # Arrange
        username = "USER_SENTINEL"
        password = "PASSWORD_SENTINEL"
        mock_auth_repository.login.side_effect = MyVerisureAuthenticationError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(
            MyVerisureAuthenticationError, match="Connection failed"
        ):
            await auth_use_case.login(username, password)

    @pytest.mark.asyncio
    async def test_login_preserves_typed_otp_challenge(self, auth_use_case, mock_auth_repository):
        """OTP challenge metadata survives the repository/application boundary."""
        from ....api.models.dto.auth_dto import PhoneDTO

        mock_auth_repository.login.side_effect = MyVerisureOTPError(
            "OTP required",
            phones=[PhoneDTO(id=7, phone="[REDACTED]", record_id=7)],
            otp_hash="[REDACTED]",
        )

        with pytest.raises(MyVerisureOTPError):
            await auth_use_case.login("USER_SENTINEL", "PASSWORD_SENTINEL")

        assert auth_use_case.get_available_phones() == [
            {
                "id": 7,
                "phone": "[REDACTED]",
                "record_id": 7,
            }
        ]

    @pytest.mark.asyncio
    async def test_login_rejects_malformed_otp_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        mock_auth_repository.login.side_effect = MyVerisureOTPError(
            "OTP metadata invalid",
            phones=[],
            otp_hash=None,
        )

        with pytest.raises(MyVerisureAuthenticationError, match="challenge"):
            await auth_use_case.login("USER_SENTINEL", "PASSWORD_SENTINEL")

        with pytest.raises(MyVerisureConnectionError, match="challenge"):
            auth_use_case.get_available_phones()

    @pytest.mark.asyncio
    async def test_login_rejects_otp_challenge_with_invalid_phone_binding(
        self, auth_use_case, mock_auth_repository
    ):
        from ....api.models.dto.auth_dto import PhoneDTO

        mock_auth_repository.login.side_effect = MyVerisureOTPError(
            "OTP metadata invalid",
            phones=[PhoneDTO(id=1, phone="PHONE_SENTINEL", record_id=None)],
            otp_hash="HASH_SENTINEL",
        )

        with pytest.raises(MyVerisureAuthenticationError, match="challenge"):
            await auth_use_case.login("USER_SENTINEL", "PASSWORD_SENTINEL")

    def test_get_available_phones(self, auth_use_case, mock_auth_repository):
        """Test getting available phones."""
        # Arrange
        expected_phone_ids = [1, 2]

        auth_use_case._otp_data = OTPData(
            phones=[
                Phone(id=1, phone="PHONE_ONE_SENTINEL", record_id=11),
                Phone(id=2, phone="PHONE_TWO_SENTINEL", record_id=12),
            ],
            otp_hash="HASH_SENTINEL",
        )

        # Act
        phones = auth_use_case.get_available_phones()

        # Assert
        assert [phone["id"] for phone in phones] == expected_phone_ids
        assert [phone["phone"] for phone in phones] == [
            "PHONE_ONE_SENTINEL",
            "PHONE_TWO_SENTINEL",
        ]
        assert [phone["record_id"] for phone in phones] == [11, 12]
        # Note: get_available_phones doesn't call the repository, it uses internal state

    @pytest.mark.asyncio
    async def test_send_otp_requires_selected_phone(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=1, phone="PHONE_SENTINEL", record_id=1)],
            otp_hash="OTP_HASH_SENTINEL",
        )
        with pytest.raises(MyVerisureOTPError, match="selected"):
            await auth_use_case.send_otp(1)
        mock_auth_repository.send_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_otp_rejects_record_id_not_matching_selected_phone(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=1, phone="PHONE_SENTINEL", record_id=1)],
            otp_hash="OTP_HASH_SENTINEL",
        )
        assert auth_use_case.select_phone(1) is True
        with pytest.raises(MyVerisureOTPError, match="record"):
            await auth_use_case.send_otp(2)
        mock_auth_repository.send_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_resending_otp_does_not_reset_original_budget_or_expiry(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=1, phone="PHONE_SENTINEL", record_id=1)],
            otp_hash="OTP_HASH_SENTINEL",
        )
        auth_use_case.select_phone(1)
        auth_use_case._otp_attempts = 2
        original_expiry = time.monotonic() + 120
        auth_use_case._otp_expires_at = original_expiry
        mock_auth_repository.send_otp.return_value = True

        assert await auth_use_case.send_otp(1) is True
        assert auth_use_case._otp_attempts == 2
        assert auth_use_case._otp_expires_at == original_expiry

    @pytest.mark.asyncio
    async def test_send_otp_rejects_non_positive_or_boolean_record_id(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=1, phone="PHONE_SENTINEL", record_id=1)],
            otp_hash="OTP_HASH_SENTINEL",
        )
        auth_use_case.select_phone(1)
        for record_id in (0, -1, True):
            with pytest.raises(MyVerisureOTPError, match="record"):
                await auth_use_case.send_otp(record_id)
        mock_auth_repository.send_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_send_otp_success(self, auth_use_case, mock_auth_repository):
        record_id = 1
        otp_hash = "VALUE_HASH"
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=record_id, phone="PHONE_SENTINEL", record_id=record_id)],
            otp_hash=otp_hash,
        )
        auth_use_case.select_phone(record_id)
        mock_auth_repository.send_otp.return_value = True

        result = await auth_use_case.send_otp(record_id, otp_hash)

        assert result is True
        mock_auth_repository.send_otp.assert_called_once_with(record_id, otp_hash)

    @pytest.mark.asyncio
    async def test_send_otp_failure(self, auth_use_case, mock_auth_repository):
        record_id = 1
        otp_hash = "VALUE_HASH"
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=record_id, phone="PHONE_SENTINEL", record_id=record_id)],
            otp_hash=otp_hash,
        )
        auth_use_case.select_phone(record_id)
        mock_auth_repository.send_otp.return_value = False

        result = await auth_use_case.send_otp(record_id, otp_hash)

        assert result is False
        mock_auth_repository.send_otp.assert_called_once_with(record_id, otp_hash)

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
            hash="HASH_SENTINEL",
        )

        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")

        # Act
        result = await auth_use_case.verify_otp(otp_code)

        # Assert
        assert result.success is True
        assert result.message == "OTP verification successful"
        mock_auth_repository.verify_otp.assert_called_once_with(otp_code)

    @pytest.mark.asyncio
    async def test_verify_otp_rejects_without_active_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = None

        with pytest.raises(MyVerisureOTPError, match="active OTP challenge"):
            await auth_use_case.verify_otp("123456")

        mock_auth_repository.verify_otp.assert_not_called()

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

        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")

        # Act
        result = await auth_use_case.verify_otp(otp_code)

        # Assert
        assert result.success is False
        assert result.message == "OTP verification failed"
        mock_auth_repository.verify_otp.assert_called_once_with(otp_code)

    @pytest.mark.asyncio
    async def test_verify_otp_retryable_provider_rejection_preserves_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        auth_use_case._otp_expires_at = time.monotonic() + 300
        mock_auth_repository.verify_otp.side_effect = MyVerisureOTPError(
            "rejected", retryable=True, code="invalid_code"
        )

        for _ in range(2):
            with pytest.raises(MyVerisureOTPError, match="rejected"):
                await auth_use_case.verify_otp("123456")
            assert auth_use_case._otp_data is not None

        with pytest.raises(MyVerisureOTPError, match="rejected"):
            await auth_use_case.verify_otp("123456")

        assert auth_use_case._otp_data is None
        assert mock_auth_repository.verify_otp.await_count == 3

    @pytest.mark.asyncio
    async def test_verify_otp_terminal_provider_rejection_invalidates_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        auth_use_case._otp_expires_at = time.monotonic() + 300
        mock_auth_repository.verify_otp.side_effect = MyVerisureOTPError(
            "challenge expired", retryable=False, code="terminal"
        )

        with pytest.raises(MyVerisureOTPError, match="expired"):
            await auth_use_case.verify_otp("123456")

        assert auth_use_case._otp_data is None
        mock_auth_repository.invalidate_otp_challenge.assert_called()

    @pytest.mark.asyncio
    async def test_send_otp_rejects_challenge_without_ttl(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(
            phones=[Phone(id=1, phone="PHONE_SENTINEL", record_id=70)],
            otp_hash="HASH_SENTINEL",
        )
        auth_use_case._selected_phone = auth_use_case._otp_data.phones[0]
        auth_use_case._otp_expires_at = None

        with pytest.raises(MyVerisureOTPError, match="challenge"):
            await auth_use_case.send_otp(70)

        mock_auth_repository.send_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_verify_otp_rejects_challenge_without_ttl(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        auth_use_case._otp_expires_at = None

        with pytest.raises(MyVerisureOTPError, match="challenge"):
            await auth_use_case.verify_otp("123456")

        mock_auth_repository.verify_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_verify_otp_rejects_expired_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        auth_use_case._otp_expires_at = time.monotonic() - 1

        with pytest.raises(MyVerisureOTPError, match="expired"):
            await auth_use_case.verify_otp("123456")

        mock_auth_repository.verify_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_verify_otp_rejects_exhausted_challenge(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        auth_use_case._otp_expires_at = time.monotonic() + 300
        auth_use_case._otp_attempts = 3

        with pytest.raises(MyVerisureOTPError, match="attempts"):
            await auth_use_case.verify_otp("123456")

        mock_auth_repository.verify_otp.assert_not_awaited()

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

        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")

        # Act & Assert
        with pytest.raises(MyVerisureOTPError, match="Invalid OTP"):
            await auth_use_case.verify_otp(otp_code)

    @pytest.mark.asyncio
    async def test_verify_otp_preserves_post_otp_device_authorization_failure(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        mock_auth_repository.verify_otp.side_effect = MyVerisureDeviceAuthorizationError(
            "device authorization failed"
        )

        with pytest.raises(MyVerisureDeviceAuthorizationError):
            await auth_use_case.verify_otp("123456")

        assert auth_use_case._otp_attempts == 0

    @pytest.mark.asyncio
    async def test_verify_otp_does_not_consume_attempt_on_persistence_failure(
        self, mock_auth_repository
    ):
        session_persistence = Mock()
        session_persistence.persist_result = AsyncMock(
            side_effect=MyVerisurePersistenceError("Session persistence failed")
        )
        auth_use_case = AuthUseCaseImpl(
            auth_repository=mock_auth_repository,
            session_persistence=session_persistence,
        )
        auth_use_case._otp_expires_at = time.monotonic() + 300
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        mock_auth_repository.verify_otp.return_value = AuthResult(
            success=True, message="success", hash="HASH_SENTINEL"
        )

        with pytest.raises(MyVerisurePersistenceError, match="Session persistence failed"):
            await auth_use_case.verify_otp("123456")

        assert auth_use_case._otp_attempts == 0
        assert auth_use_case._otp_data is None

    @pytest.mark.asyncio
    async def test_verify_otp_rejects_empty_code_without_repository_call(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")

        with pytest.raises(MyVerisureOTPError, match="format"):
            await auth_use_case.verify_otp(" ")

        assert auth_use_case._otp_attempts == 0
        mock_auth_repository.verify_otp.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_verify_otp_consumes_challenge_after_success(
        self, mock_auth_repository
    ):
        session_persistence = Mock()
        session_persistence.persist_result = AsyncMock()
        auth_use_case = AuthUseCaseImpl(
            auth_repository=mock_auth_repository,
            session_persistence=session_persistence,
        )
        auth_use_case._otp_expires_at = time.monotonic() + 300
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="[REDACTED]")
        mock_auth_repository.verify_otp.return_value = AuthResult(
            success=True,
            message="[REDACTED]",
            hash="[REDACTED]",
            refresh_token="[REDACTED]",
        )

        await auth_use_case.verify_otp("123456")

        with pytest.raises(MyVerisureOTPError, match="challenge|attempts"):
            await auth_use_case.verify_otp("123456")
        mock_auth_repository.verify_otp.assert_awaited_once_with("123456")
        session_persistence.persist_result.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_verify_otp_propagates_timeout_without_consuming_attempt(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        mock_auth_repository.verify_otp.side_effect = TimeoutError("offline")

        with pytest.raises(TimeoutError, match="offline"):
            await auth_use_case.verify_otp("123456")

        assert auth_use_case._otp_attempts == 0

    @pytest.mark.asyncio
    async def test_verify_otp_propagates_aiohttp_without_consuming_attempt(
        self, auth_use_case, mock_auth_repository
    ):
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")
        mock_auth_repository.verify_otp.side_effect = MyVerisureConnectionError("offline")

        with pytest.raises(MyVerisureConnectionError, match="offline"):
            await auth_use_case.verify_otp("123456")

        assert auth_use_case._otp_attempts == 0

    @pytest.mark.asyncio
    async def test_verify_otp_persists_authenticated_session(
        self, mock_auth_repository
    ):
        """Successful OTP verification must persist the authenticated session."""
        session_persistence = Mock()
        session_persistence.persist_result = AsyncMock()
        auth_use_case = AuthUseCaseImpl(
            auth_repository=mock_auth_repository,
            session_persistence=session_persistence,
        )
        auth_use_case._otp_expires_at = time.monotonic() + 300
        expected_result = AuthResult(
            success=True,
            hash="otp-[REDACTED]",
            refresh_token="otp-[REDACTED]",
            message="OTP verification successful",
        )
        mock_auth_repository.verify_otp.return_value = expected_result
        auth_use_case._otp_data = OTPData(phones=[], otp_hash="HASH_SENTINEL")

        result = await auth_use_case.verify_otp("123456")

        assert result == expected_result
        session_persistence.persist_result.assert_awaited_once_with(expected_result)


if __name__ == "__main__":
    pytest.main([__file__])

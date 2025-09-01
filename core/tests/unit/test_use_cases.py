"""Unit tests for use cases."""

import pytest
from unittest.mock import Mock, AsyncMock

from api.models.domain.auth import Auth, AuthResult
from api.models.domain.session import SessionData, DeviceIdentifiers
from api.models.domain.installation import Installation, InstallationServices
from api.models.domain.alarm import AlarmStatus, ArmResult, DisarmResult

from use_cases.implementations.auth_use_case_impl import AuthUseCaseImpl
from use_cases.implementations.session_use_case_impl import SessionUseCaseImpl
from use_cases.implementations.installation_use_case_impl import (
    InstallationUseCaseImpl,
)
from use_cases.implementations.alarm_use_case_impl import AlarmUseCaseImpl


class TestAuthUseCaseImpl:
    """Test AuthUseCaseImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_auth_repository = Mock()
        self.use_case = AuthUseCaseImpl(self.mock_auth_repository)

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        # Arrange
        username = "test_user"
        password = "test_pass"

        expected_result = AuthResult(
            success=True,
            message="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
        )

        self.mock_auth_repository.login = AsyncMock(
            return_value=expected_result
        )

        # Act
        result = await self.use_case.login(username, password)

        # Assert
        assert result.success is True
        assert result.message == "Login successful"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"

        # Verify repository was called with correct domain models
        call_args = self.mock_auth_repository.login.call_args
        auth_arg = call_args[0][0]  # First positional argument
        device_arg = call_args[0][1]  # Second positional argument

        assert isinstance(auth_arg, Auth)
        assert auth_arg.username == username
        assert auth_arg.password == password

        assert isinstance(device_arg, DeviceIdentifiers)
        assert device_arg.device_name == "HomeAssistant"

    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test failed login."""
        # Arrange
        username = "test_user"
        password = "test_pass"

        expected_result = AuthResult(success=False, message="Login failed")

        self.mock_auth_repository.login = AsyncMock(
            return_value=expected_result
        )

        # Act
        result = await self.use_case.login(username, password)

        # Assert
        assert result.success is False
        assert result.message == "Login failed"

    @pytest.mark.asyncio
    async def test_send_otp_success(self):
        """Test successful OTP send."""
        # Arrange
        record_id = 123
        otp_hash = "test_hash"

        self.mock_auth_repository.send_otp = AsyncMock(return_value=True)

        # Act
        result = await self.use_case.send_otp(record_id, otp_hash)

        # Assert
        assert result is True
        self.mock_auth_repository.send_otp.assert_called_once_with(
            record_id, otp_hash
        )

    @pytest.mark.asyncio
    async def test_send_otp_failure(self):
        """Test failed OTP send."""
        # Arrange
        record_id = 123
        otp_hash = "test_hash"

        self.mock_auth_repository.send_otp = AsyncMock(return_value=False)

        # Act
        result = await self.use_case.send_otp(record_id, otp_hash)

        # Assert
        assert result is False
        self.mock_auth_repository.send_otp.assert_called_once_with(
            record_id, otp_hash
        )

    def test_get_available_phones_empty(self):
        """Test getting available phones when no OTP data."""
        # Act
        result = self.use_case.get_available_phones()

        # Assert
        assert result == []

    def test_select_phone_no_otp_data(self):
        """Test selecting phone when no OTP data."""
        # Act
        result = self.use_case.select_phone(1)

        # Assert
        assert result is False


class TestSessionUseCaseImpl:
    """Test SessionUseCaseImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session_repository = Mock()
        self.use_case = SessionUseCaseImpl(self.mock_session_repository)

    @pytest.mark.asyncio
    async def test_load_session_success(self):
        """Test successful session load."""
        # Arrange
        file_path = "/test/path/session.json"

        session_data = SessionData(
            cookies={"session": "cookie_value"},
            session_data={"user": "test_user"},
            hash="test_hash",
            user="test_user",
            device_identifiers=None,
            saved_time=1640995200,
        )

        self.mock_session_repository.load_session = AsyncMock(
            return_value=session_data
        )

        # Act
        result = await self.use_case.load_session(file_path)

        # Assert
        assert result is True
        assert self.use_case._current_session_data == session_data

        self.mock_session_repository.load_session.assert_called_once_with(
            file_path
        )

    @pytest.mark.asyncio
    async def test_load_session_failure(self):
        """Test failed session load."""
        # Arrange
        file_path = "/test/path/session.json"

        self.mock_session_repository.load_session = AsyncMock(
            return_value=None
        )

        # Act
        result = await self.use_case.load_session(file_path)

        # Assert
        assert result is False
        assert self.use_case._current_session_data is None

    @pytest.mark.asyncio
    async def test_save_session_success(self):
        """Test successful session save."""
        # Arrange
        file_path = "/test/path/session.json"

        session_data = SessionData(
            cookies={"session": "cookie_value"},
            session_data={"user": "test_user"},
            hash="test_hash",
            user="test_user",
            device_identifiers=None,
            saved_time=1640995200,
        )

        self.use_case._current_session_data = session_data
        self.mock_session_repository.save_session = AsyncMock(
            return_value=True
        )

        # Act
        result = await self.use_case.save_session(file_path)

        # Assert
        assert result is True
        self.mock_session_repository.save_session.assert_called_once_with(
            file_path, session_data
        )

    @pytest.mark.asyncio
    async def test_save_session_no_data(self):
        """Test session save with no data."""
        # Arrange
        file_path = "/test/path/session.json"

        self.use_case._current_session_data = None

        # Act
        result = await self.use_case.save_session(file_path)

        # Assert
        assert result is False
        self.mock_session_repository.save_session.assert_not_called()

    def test_is_session_valid_with_data(self):
        """Test session validity with data."""
        # Arrange
        session_data = SessionData(
            cookies={},
            session_data={},
            hash="test_hash",
            user="test_user",
            device_identifiers=None,
            saved_time=1640995200,
        )

        self.use_case._current_session_data = session_data
        self.mock_session_repository.is_session_valid.return_value = True

        # Act
        result = self.use_case.is_session_valid()

        # Assert
        assert result is True
        self.mock_session_repository.is_session_valid.assert_called_once_with(
            session_data
        )

    def test_is_session_valid_no_data(self):
        """Test session validity with no data."""
        # Arrange
        self.use_case._current_session_data = None

        # Act
        result = self.use_case.is_session_valid()

        # Assert
        assert result is False
        self.mock_session_repository.is_session_valid.assert_not_called()


class TestInstallationUseCaseImpl:
    """Test InstallationUseCaseImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_installation_repository = Mock()
        self.use_case = InstallationUseCaseImpl(
            self.mock_installation_repository
        )

    @pytest.mark.asyncio
    async def test_get_installations_success(self):
        """Test successful installations retrieval."""
        # Arrange
        installations = [
            Installation(
                numinst="12345",
                alias="Home",
                panel="PROTOCOL",
                type="ALARM",
                name="John",
                surname="Doe",
                address="123 Main St",
                city="Madrid",
                postcode="28001",
                province="Madrid",
                email="john@example.com",
                phone="+34600000000",
            )
        ]

        self.mock_installation_repository.get_installations = AsyncMock(
            return_value=installations
        )

        # Act
        result = await self.use_case.get_installations()

        # Assert
        assert len(result) == 1
        assert result[0].numinst == "12345"
        assert result[0].alias == "Home"

        self.mock_installation_repository.get_installations.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_installation_services_success(self):
        """Test successful installation services retrieval."""
        # Arrange
        installation_id = "12345"

        services = InstallationServices(
            success=True,
            message="Success",
            language="es",
            installation_data={},
            services=[],
        )

        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=services)
        )

        # Act
        result = await self.use_case.get_installation_services(installation_id)

        # Assert
        assert result.success is True
        assert result.message == "Success"
        assert result.language == "es"

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id, False)

    @pytest.mark.asyncio
    async def test_get_installation_services_force_refresh(self):
        """Test installation services retrieval with force refresh."""
        # Arrange
        installation_id = "12345"
        force_refresh = True

        services = InstallationServices(
            success=True,
            message="Success",
            language="es",
            installation_data={},
            services=[],
        )

        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=services)
        )

        # Act
        result = await self.use_case.get_installation_services(
            installation_id, force_refresh
        )

        # Assert
        assert result.success is True

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id, True)




class TestAlarmUseCaseImpl:
    """Test AlarmUseCaseImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_alarm_repository = Mock()
        self.mock_installation_repository = Mock()
        self.use_case = AlarmUseCaseImpl(
            self.mock_alarm_repository, self.mock_installation_repository
        )

    @pytest.mark.asyncio
    async def test_get_alarm_status_success(self):
        """Test successful alarm status retrieval."""
        # Arrange
        installation_id = "12345"

        # Mock installation services
        mock_services = Mock()
        mock_services.installation_data = {"panel": "PROTOCOL"}
        mock_services.capabilities = "default_capabilities"
        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=mock_services)
        )

        alarm_status = AlarmStatus(
            success=True,
            message="Alarm status retrieved",
            status="DISARMED",
            numinst=installation_id,
        )

        self.mock_alarm_repository.get_alarm_status = AsyncMock(
            return_value=alarm_status
        )

        # Act
        result = await self.use_case.get_alarm_status(installation_id)

        # Assert
        assert result.success is True
        assert result.message == "Alarm status retrieved"
        assert result.status == "DISARMED"
        assert result.numinst == installation_id

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id)
        self.mock_alarm_repository.get_alarm_status.assert_called_once_with(
            installation_id, "PROTOCOL", "default_capabilities"
        )

    @pytest.mark.asyncio
    async def test_arm_away_success(self):
        """Test successful arm away."""
        # Arrange
        installation_id = "12345"

        # Mock installation services
        mock_services = Mock()
        mock_services.installation_data = {"panel": "PROTOCOL"}
        mock_services.capabilities = "default_capabilities"
        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=mock_services)
        )

        arm_result = ArmResult(
            success=True, message="Alarm armed successfully with request ARM1"
        )

        self.mock_alarm_repository.arm_panel = AsyncMock(
            return_value=arm_result
        )

        # Act
        result = await self.use_case.arm_away(installation_id)

        # Assert
        assert result is True

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id)
        self.mock_alarm_repository.arm_panel.assert_called_once_with(
            installation_id, "ARM1", "PROTOCOL", "E"
        )

    @pytest.mark.asyncio
    async def test_arm_away_failure(self):
        """Test failed arm away."""
        # Arrange
        installation_id = "12345"

        # Mock installation services
        mock_services = Mock()
        mock_services.installation_data = {"panel": "PROTOCOL"}
        mock_services.capabilities = "default_capabilities"
        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=mock_services)
        )

        arm_result = ArmResult(success=False, message="Failed to arm alarm")

        self.mock_alarm_repository.arm_panel = AsyncMock(
            return_value=arm_result
        )

        # Act
        result = await self.use_case.arm_away(installation_id)

        # Assert
        assert result is False

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_arm_home_success(self):
        """Test successful arm home."""
        # Arrange
        installation_id = "12345"

        # Mock installation services
        mock_services = Mock()
        mock_services.installation_data = {"panel": "PROTOCOL"}
        mock_services.capabilities = "default_capabilities"
        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=mock_services)
        )

        arm_result = ArmResult(
            success=True, message="Alarm armed successfully with request PERI1"
        )

        self.mock_alarm_repository.arm_panel = AsyncMock(
            return_value=arm_result
        )

        # Act
        result = await self.use_case.arm_home(installation_id)

        # Assert
        assert result is True

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id)
        self.mock_alarm_repository.arm_panel.assert_called_once_with(
            installation_id, "PERI1", "PROTOCOL", "E"
        )

    @pytest.mark.asyncio
    async def test_arm_night_success(self):
        """Test successful arm night."""
        # Arrange
        installation_id = "12345"

        # Mock installation services
        mock_services = Mock()
        mock_services.installation_data = {"panel": "PROTOCOL"}
        mock_services.capabilities = "default_capabilities"
        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=mock_services)
        )

        arm_result = ArmResult(
            success=True,
            message="Alarm armed successfully with request ARMNIGHT1",
        )

        self.mock_alarm_repository.arm_panel = AsyncMock(
            return_value=arm_result
        )

        # Act
        result = await self.use_case.arm_night(installation_id)

        # Assert
        assert result is True

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id)
        self.mock_alarm_repository.arm_panel.assert_called_once_with(
            installation_id, "ARMNIGHT1", "PROTOCOL", "E"
        )

    @pytest.mark.asyncio
    async def test_disarm_success(self):
        """Test successful disarm."""
        # Arrange
        installation_id = "12345"

        # Mock installation services
        mock_services = Mock()
        mock_services.installation_data = {"panel": "PROTOCOL"}
        mock_services.capabilities = "default_capabilities"
        self.mock_installation_repository.get_installation_services = (
            AsyncMock(return_value=mock_services)
        )

        disarm_result = DisarmResult(
            success=True, message="Alarm disarmed successfully"
        )

        self.mock_alarm_repository.disarm_panel = AsyncMock(
            return_value=disarm_result
        )

        # Act
        result = await self.use_case.disarm(installation_id)

        # Assert
        assert result is True

        self.mock_installation_repository.get_installation_services.\
            assert_called_once_with(installation_id)
        self.mock_alarm_repository.disarm_panel.assert_called_once_with(
            installation_id, "PROTOCOL"
        )

    @pytest.mark.asyncio
    async def test_disarm_failure(self):
        """Test failed disarm."""
        # Arrange
        installation_id = "12345"

        disarm_result = DisarmResult(
            success=False, message="Failed to disarm alarm"
        )

        self.mock_alarm_repository.disarm_panel = AsyncMock(
            return_value=disarm_result
        )

        # Act
        result = await self.use_case.disarm(installation_id)

        # Assert
        assert result is False

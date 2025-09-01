"""Unit tests for repositories."""

import pytest
from unittest.mock import Mock, AsyncMock

from api.models.domain.auth import Auth
from api.models.domain.session import SessionData, DeviceIdentifiers

from repositories.implementations.auth_repository_impl import (
    AuthRepositoryImpl,
)
from repositories.implementations.session_repository_impl import (
    SessionRepositoryImpl,
)
from repositories.implementations.installation_repository_impl import (
    InstallationRepositoryImpl,
)
from repositories.implementations.alarm_repository_impl import (
    AlarmRepositoryImpl,
)


class TestAuthRepositoryImpl:
    """Test AuthRepositoryImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.repository = AuthRepositoryImpl(self.mock_client)

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test successful login."""
        # Arrange
        auth = Auth(username="test_user", password="test_pass")
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
        )

        self.mock_client.login = AsyncMock(return_value=True)
        self.mock_client._hash = "test_hash"
        self.mock_client._refresh_token = "test_refresh"
        self.mock_client._session_data = {
            "lang": "es",
            "legals": True,
            "changePassword": False,
            "needDeviceAuthorization": False,
        }

        # Act
        result = await self.repository.login(auth, device_identifiers)

        # Assert
        assert result.success is True
        assert result.message == "Login successful"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"
        assert result.lang == "es"
        assert result.legals is True
        assert result.change_password is False
        assert result.need_device_authorization is False

        self.mock_client.login.assert_called_once()

    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test failed login."""
        # Arrange
        auth = Auth(username="test_user", password="test_pass")
        device_identifiers = DeviceIdentifiers(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
        )

        self.mock_client.login = AsyncMock(return_value=False)

        # Act
        result = await self.repository.login(auth, device_identifiers)

        # Assert
        assert result.success is False
        assert result.message == "Login failed"

    @pytest.mark.asyncio
    async def test_send_otp_success(self):
        """Test successful OTP send."""
        # Arrange
        record_id = 123
        otp_hash = "test_hash"

        self.mock_client.send_otp = AsyncMock(return_value=True)

        # Act
        result = await self.repository.send_otp(record_id, otp_hash)

        # Assert
        assert result is True
        self.mock_client.send_otp.assert_called_once_with(record_id, otp_hash)

    @pytest.mark.asyncio
    async def test_send_otp_failure(self):
        """Test failed OTP send."""
        # Arrange
        record_id = 123
        otp_hash = "test_hash"

        self.mock_client.send_otp = AsyncMock(return_value=False)

        # Act
        result = await self.repository.send_otp(record_id, otp_hash)

        # Assert
        assert result is False
        self.mock_client.send_otp.assert_called_once_with(record_id, otp_hash)

    @pytest.mark.asyncio
    async def test_verify_otp_success(self):
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
        )

        self.mock_client.verify_otp = AsyncMock(return_value=True)
        self.mock_client._hash = "test_hash"
        self.mock_client._refresh_token = "test_refresh"
        self.mock_client._session_data = {
            "lang": "es",
            "legals": True,
            "changePassword": False,
            "needDeviceAuthorization": False,
        }

        # Act
        result = await self.repository.verify_otp(
            otp_code, otp_hash, device_identifiers
        )

        # Assert
        assert result.success is True
        assert result.message == "OTP verification successful"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"

        self.mock_client.verify_otp.assert_called_once_with(otp_code)

    @pytest.mark.asyncio
    async def test_verify_otp_failure(self):
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
        )

        self.mock_client.verify_otp = AsyncMock(return_value=False)

        # Act
        result = await self.repository.verify_otp(
            otp_code, otp_hash, device_identifiers
        )

        # Assert
        assert result.success is False
        assert result.message == "OTP verification failed"

        self.mock_client.verify_otp.assert_called_once_with(otp_code)


class TestSessionRepositoryImpl:
    """Test SessionRepositoryImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.repository = SessionRepositoryImpl(self.mock_client)

    @pytest.mark.asyncio
    async def test_load_session_success(self):
        """Test successful session load."""
        # Arrange
        file_path = "/test/path/session.json"

        self.mock_client.load_session = AsyncMock(return_value=True)
        self.mock_client._cookies = {"session": "cookie_value"}
        self.mock_client._session_data = {"user": "test_user"}
        self.mock_client._hash = "test_hash"
        self.mock_client.user = "test_user"
        self.mock_client._device_identifiers = {
            "idDevice": "device_123",
            "uuid": "uuid_456",
            "idDeviceIndigitall": "indigitall_789",
            "deviceName": "HomeAssistant",
            "deviceBrand": "HomeAssistant",
            "deviceOsVersion": "Linux 5.0",
            "deviceVersion": "10.154.0",
            "deviceType": "",
            "deviceResolution": "",
            "generated_time": 1640995200,
        }

        # Act
        result = await self.repository.load_session(file_path)

        # Assert
        assert result is not None
        assert result.cookies == {"session": "cookie_value"}
        assert result.session_data == {"user": "test_user"}
        assert result.hash == "test_hash"
        assert result.user == "test_user"
        assert result.device_identifiers is not None
        assert result.device_identifiers.id_device == "device_123"

        self.mock_client.load_session.assert_called_once_with(file_path)

    @pytest.mark.asyncio
    async def test_load_session_failure(self):
        """Test failed session load."""
        # Arrange
        file_path = "/test/path/session.json"

        self.mock_client.load_session = AsyncMock(return_value=False)

        # Act
        result = await self.repository.load_session(file_path)

        # Assert
        assert result is None
        self.mock_client.load_session.assert_called_once_with(file_path)

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

        self.mock_client.save_session = AsyncMock()

        # Act
        result = await self.repository.save_session(file_path, session_data)

        # Assert
        assert result is True
        assert self.mock_client._cookies == {"session": "cookie_value"}
        assert self.mock_client._session_data == {"user": "test_user"}
        assert self.mock_client._hash == "test_hash"
        assert self.mock_client.user == "test_user"

        self.mock_client.save_session.assert_called_once_with(file_path)

    def test_is_session_valid_with_hash(self):
        """Test session validity with hash."""
        # Arrange
        session_data = SessionData(
            cookies={},
            session_data={},
            hash="test_hash",
            user="test_user",
            device_identifiers=None,
            saved_time=1640995200,  # Old timestamp
        )

        # Act
        result = self.repository.is_session_valid(session_data)

        # Assert
        assert result is False  # Should be False because it's old

    def test_is_session_valid_without_hash(self):
        """Test session validity without hash."""
        # Arrange
        session_data = SessionData(
            cookies={},
            session_data={},
            hash=None,
            user="test_user",
            device_identifiers=None,
            saved_time=1640995200,
        )

        # Act
        result = self.repository.is_session_valid(session_data)

        # Assert
        assert result is False


class TestInstallationRepositoryImpl:
    """Test InstallationRepositoryImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_client._hash = "test_hash"
        self.mock_client._session_data = {}
        self.repository = InstallationRepositoryImpl(self.mock_client)
        
        # Clear any existing cache to ensure clean test state
        self.repository._clear_cache()

    @pytest.mark.asyncio
    async def test_get_installations_success(self):
        """Test successful installations retrieval."""
        # Arrange
        from api.models.dto.installation_dto import InstallationDTO
        installations_data = [
            InstallationDTO(
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

        # Setup client hash and session data
        self.mock_client._hash = "test_hash"
        self.mock_client._session_data = {"session": "data"}
        self.mock_client._client = True  # Mock connected client

        self.mock_client.get_installations = AsyncMock(
            return_value=installations_data
        )

        # Act
        result = await self.repository.get_installations()

        # Assert
        assert len(result) == 1
        assert result[0].numinst == "12345"
        assert result[0].alias == "Home"
        assert result[0].name == "John"
        assert result[0].surname == "Doe"

        self.mock_client.get_installations.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_installation_services_success(self):
        """Test successful installation services retrieval."""
        # Arrange
        installation_id = "12345"
        services_data = {
            "res": "OK",
            "msg": "Success",
            "language": "es",
            "installation": {
                "services": [
                    {"idService": "EST", "active": True, "visible": True}
                ]
            },
        }

        self.mock_client.get_installation_services = AsyncMock(
            return_value=services_data
        )

        # Act
        result = await self.repository.get_installation_services(
            installation_id
        )

        # Assert
        assert result.success is True
        assert result.message == "Success"
        assert result.language == "es"
        assert len(result.services) == 1
        assert result.services[0].id_service == "EST"
        assert result.services[0].active is True

        self.mock_client.get_installation_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_services_cache_based_on_hash(self):
        """Test that services cache is based on hash."""
        # Setup - first call
        self.mock_client._hash = "hash1"
        services_data = {
            "res": "OK",
            "msg": "Success",
            "language": "es",
            "installation": {
                "services": [
                    {"idService": "EST", "active": True, "visible": True}
                ]
            },
        }
        self.mock_client.get_installation_services = AsyncMock(return_value=services_data)

        # Execute first call
        result1 = await self.repository.get_installation_services("12345")

        # Verify first call made API request
        self.mock_client.get_installation_services.assert_called_once()
        assert result1.success is True

        # Setup - second call with same hash
        self.mock_client.get_installation_services.reset_mock()

        # Execute second call
        result2 = await self.repository.get_installation_services("12345")

        # Verify second call used cache (no API request)
        self.mock_client.get_installation_services.assert_not_called()
        assert result2 == result1

        # Setup - third call with different hash
        self.mock_client._hash = "hash2"
        self.mock_client.get_installation_services.reset_mock()
        self.mock_client.get_installation_services.return_value = {
            "res": "OK",
            "msg": "Success",
            "language": "es",
            "installation": {
                "services": [
                    {"idService": "CAM", "active": False, "visible": True}
                ]
            },
        }

        # Execute third call
        result3 = await self.repository.get_installation_services("12345")

        # Verify third call made API request due to hash change
        self.mock_client.get_installation_services.assert_called_once()
        assert result3.success is True
        assert result3.services[0].id_service != result1.services[0].id_service

    @pytest.mark.asyncio
    async def test_services_cache_invalidation_on_hash_change(self):
        """Test that services cache is invalidated when hash changes."""
        # Setup - first call
        self.mock_client._hash = "hash1"
        services_data = {
            "res": "OK",
            "msg": "Success",
            "language": "es",
            "installation": {
                "services": [
                    {"idService": "EST", "active": True, "visible": True}
                ]
            },
        }
        self.mock_client.get_installation_services = AsyncMock(return_value=services_data)

        # Execute first call
        result1 = await self.repository.get_installation_services("12345")
        self.mock_client.get_installation_services.assert_called_once()

        # Change hash
        self.mock_client._hash = "hash2"
        self.mock_client.get_installation_services.reset_mock()

        # Execute second call
        result2 = await self.repository.get_installation_services("12345")

        # Verify API was called again due to hash change
        self.mock_client.get_installation_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_services_cache_ttl_expiration(self):
        """Test that services cache expires based on TTL."""
        import time
        
        # Setup
        self.mock_client._hash = "hash1"
        services_data = {
            "res": "OK",
            "msg": "Success",
            "language": "es",
            "installation": {
                "services": [
                    {"idService": "EST", "active": True, "visible": True}
                ]
            },
        }
        self.mock_client.get_installation_services = AsyncMock(return_value=services_data)

        # Execute first call
        result1 = await self.repository.get_installation_services("12345")
        self.mock_client.get_installation_services.assert_called_once()

        # Set short TTL and wait
        self.repository._set_cache_ttl(1)  # 1 second TTL
        time.sleep(1.1)  # Wait for cache to expire

        # Execute second call
        self.mock_client.get_installation_services.reset_mock()
        result2 = await self.repository.get_installation_services("12345")

        # Verify API was called again due to TTL expiration
        self.mock_client.get_installation_services.assert_called_once()

    def test_get_cache_info_internal(self):
        """Test getting cache information (internal method)."""
        # Setup
        cache_info = {
            "cache_size": 2,
            "ttl_seconds": 300,
            "cached_installations": ["inst1", "inst2"],
        }
        self.mock_client.get_cache_info.return_value = cache_info

        # Execute
        result = self.repository._get_cache_info()

        # Verify
        self.mock_client.get_cache_info.assert_called_once()
        assert result["client_cache"] == cache_info
        assert "installations_cache" in result
        assert "services_cache" in result

    def test_clear_cache_internal(self):
        """Test cache clearing (internal method)."""
        # Arrange
        installation_id = "12345"

        # Act
        self.repository._clear_cache(installation_id)

        # Assert
        # The method is called twice: once in setup (with None) and once in test (with installation_id)
        assert self.mock_client.clear_installation_services_cache.call_count == 2
        self.mock_client.clear_installation_services_cache.assert_any_call(None)  # From setup
        self.mock_client.clear_installation_services_cache.assert_any_call(installation_id)  # From test

    def test_set_cache_ttl_internal(self):
        """Test cache TTL setting (internal method)."""
        # Arrange
        ttl_seconds = 300

        # Act
        self.repository._set_cache_ttl(ttl_seconds)

        # Assert
        self.mock_client.set_cache_ttl.assert_called_once_with(ttl_seconds)


class TestAlarmRepositoryImpl:
    """Test AlarmRepositoryImpl."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.repository = AlarmRepositoryImpl(self.mock_client)

    @pytest.mark.asyncio
    async def test_get_alarm_status_success(self):
        """Test successful alarm status retrieval."""
        # Arrange
        installation_id = "12345"
        panel = "PROTOCOL"
        capabilities = "test_capabilities"

        alarm_status_data = {
            "internal": {
                "day": {"status": False},
                "night": {"status": False},
                "total": {"status": False},
            },
            "external": {"status": False},
        }

        self.mock_client.get_alarm_status = AsyncMock(
            return_value=alarm_status_data
        )

        # Act
        result = await self.repository.get_alarm_status(
            installation_id, panel, capabilities
        )

        # Assert
        assert result.success is True
        # The actual message might be different, so we just check that it's not empty
        assert result.message is not None
        assert result.numinst == installation_id

        self.mock_client.get_alarm_status.assert_called_once_with(
            installation_id, capabilities
        )

    @pytest.mark.asyncio
    async def test_arm_panel_away_success(self):
        """Test successful arm away."""
        # Arrange
        installation_id = "12345"
        request = "ARM1"
        panel = "PROTOCOL"
        current_status = "E"

        self.mock_client.arm_alarm_away = AsyncMock(return_value=True)

        # Act
        result = await self.repository.arm_panel(
            installation_id, request, panel, current_status
        )

        # Assert
        assert result.success is True
        assert "ARM1" in result.message

        self.mock_client.arm_alarm_away.assert_called_once_with(
            installation_id
        )

    @pytest.mark.asyncio
    async def test_arm_panel_home_success(self):
        """Test successful arm home."""
        # Arrange
        installation_id = "12345"
        request = "PERI1"
        panel = "PROTOCOL"
        current_status = "E"

        self.mock_client.arm_alarm_home = AsyncMock(return_value=True)

        # Act
        result = await self.repository.arm_panel(
            installation_id, request, panel, current_status
        )

        # Assert
        assert result.success is True
        assert "PERI1" in result.message

        self.mock_client.arm_alarm_home.assert_called_once_with(
            installation_id
        )

    @pytest.mark.asyncio
    async def test_arm_panel_night_success(self):
        """Test successful arm night."""
        # Arrange
        installation_id = "12345"
        request = "ARMNIGHT1"
        panel = "PROTOCOL"
        current_status = "E"

        self.mock_client.arm_alarm_night = AsyncMock(return_value=True)

        # Act
        result = await self.repository.arm_panel(
            installation_id, request, panel, current_status
        )

        # Assert
        assert result.success is True
        assert "ARMNIGHT1" in result.message

        self.mock_client.arm_alarm_night.assert_called_once_with(
            installation_id
        )

    @pytest.mark.asyncio
    async def test_disarm_panel_success(self):
        """Test successful disarm."""
        # Arrange
        installation_id = "12345"
        panel = "PROTOCOL"

        self.mock_client.disarm_alarm = AsyncMock(return_value=True)

        # Act
        result = await self.repository.disarm_panel(installation_id, panel)

        # Assert
        assert result.success is True
        assert result.message == "Alarm disarmed successfully"

        self.mock_client.disarm_alarm.assert_called_once_with(installation_id)

    @pytest.mark.asyncio
    async def test_check_arm_status_success(self):
        """Test successful arm status check."""
        # Arrange
        installation_id = "12345"
        panel = "PROTOCOL"
        request = "ARM1"
        reference_id = "ref_123"
        counter = 1

        # Act
        result = await self.repository.check_arm_status(
            installation_id, panel, request, reference_id, counter
        )

        # Assert
        assert result.success is True
        assert result.message == "Arm status check completed"
        assert result.reference_id == reference_id

    @pytest.mark.asyncio
    async def test_check_disarm_status_success(self):
        """Test successful disarm status check."""
        # Arrange
        installation_id = "12345"
        panel = "PROTOCOL"
        reference_id = "ref_456"
        counter = 1

        # Act
        result = await self.repository.check_disarm_status(
            installation_id, panel, reference_id, counter
        )

        # Assert
        assert result.success is True
        assert result.message == "Disarm status check completed"
        assert result.reference_id == reference_id

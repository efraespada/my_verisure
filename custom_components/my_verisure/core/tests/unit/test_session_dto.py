"""Unit tests for SessionDTO and related DTOs."""

import pytest

from ...api.models.dto.session_dto import SessionDTO, DeviceIdentifiersDTO


class TestDeviceIdentifiersDTO:
    """Test DeviceIdentifiersDTO."""

    def test_from_dict(self):
        """Test creating DeviceIdentifiersDTO from dictionary."""
        data = {
            "idDevice": "device_123",
            "uuid": "uuid_456",
            "idDeviceIndigitall": "indigitall_789",
            "deviceName": "HomeAssistant",
            "deviceBrand": "HomeAssistant",
            "deviceOsVersion": "Linux 5.0",
            "deviceVersion": "10.154.0",
            "deviceType": "mobile",
            "deviceResolution": "1920x1080",
            "generated_time": 1640995200,
        }

        dto = DeviceIdentifiersDTO.from_dict(data)

        assert dto.id_device == "device_123"
        assert dto.uuid == "uuid_456"
        assert dto.id_device_indigitall == "indigitall_789"
        assert dto.device_name == "HomeAssistant"
        assert dto.device_brand == "HomeAssistant"
        assert dto.device_os_version == "Linux 5.0"
        assert dto.device_version == "10.154.0"
        assert dto.device_type == "mobile"
        assert dto.device_resolution == "1920x1080"
        assert dto.generated_time == 1640995200

    def test_to_dict(self):
        """Test converting DeviceIdentifiersDTO to dictionary."""
        dto = DeviceIdentifiersDTO(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
            device_type="mobile",
            device_resolution="1920x1080",
            generated_time=1640995200,
        )

        result = dto.to_dict()

        assert result["idDevice"] == "device_123"
        assert result["uuid"] == "uuid_456"
        assert result["idDeviceIndigitall"] == "indigitall_789"
        assert result["deviceName"] == "HomeAssistant"
        assert result["deviceBrand"] == "HomeAssistant"
        assert result["deviceOsVersion"] == "Linux 5.0"
        assert result["deviceVersion"] == "10.154.0"
        assert result["deviceType"] == "mobile"
        assert result["deviceResolution"] == "1920x1080"
        assert result["generated_time"] == 1640995200

    def test_from_dict_with_missing_fields(self):
        """Test creating DeviceIdentifiersDTO from dictionary with missing fields."""
        data = {
            "idDevice": "device_123",
            "uuid": "uuid_456",
        }

        dto = DeviceIdentifiersDTO.from_dict(data)

        assert dto.id_device == "device_123"
        assert dto.uuid == "uuid_456"
        assert dto.id_device_indigitall is None
        assert dto.device_name is None
        assert dto.device_brand is None
        assert dto.device_os_version is None
        assert dto.device_version is None
        assert dto.device_type is None
        assert dto.device_resolution is None
        assert dto.generated_time is None


class TestSessionDTO:
    """Test SessionDTO."""

    def test_from_dict(self):
        """Test creating SessionDTO from dictionary."""
        data = {
            "cookies": {"session": "cookie_value"},
            "session_data": {"user": "test_user"},
            "hash": "test_hash",
            "user": "test_user",
            "device_identifiers": {
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
            },
            "saved_time": 1640995200,
        }

        dto = SessionDTO.from_dict(data)

        assert dto.cookies == {"session": "cookie_value"}
        assert dto.session_data == {"user": "test_user"}
        assert dto.hash == "test_hash"
        assert dto.user == "test_user"
        assert dto.device_identifiers is not None
        assert dto.device_identifiers.id_device == "device_123"
        assert dto.saved_time == 1640995200

    def test_to_dict(self):
        """Test converting SessionDTO to dictionary."""
        device_identifiers = DeviceIdentifiersDTO(
            id_device="device_123",
            uuid="uuid_456",
            id_device_indigitall="indigitall_789",
            device_name="HomeAssistant",
            device_brand="HomeAssistant",
            device_os_version="Linux 5.0",
            device_version="10.154.0",
        )

        dto = SessionDTO(
            cookies={"session": "cookie_value"},
            session_data={"user": "test_user"},
            hash="test_hash",
            user="test_user",
            device_identifiers=device_identifiers,
            saved_time=1640995200,
        )

        result = dto.to_dict()

        assert result["cookies"] == {"session": "cookie_value"}
        assert result["session_data"] == {"user": "test_user"}
        assert result["hash"] == "test_hash"
        assert result["user"] == "test_user"
        assert result["device_identifiers"] is not None
        assert result["device_identifiers"]["idDevice"] == "device_123"
        assert result["saved_time"] == 1640995200

    def test_from_dict_with_missing_fields(self):
        """Test creating SessionDTO from dictionary with missing fields."""
        data = {
            "cookies": {"session": "cookie_value"},
        }

        dto = SessionDTO.from_dict(data)

        assert dto.cookies == {"session": "cookie_value"}
        assert dto.session_data is None
        assert dto.hash is None
        assert dto.user is None
        assert dto.device_identifiers is None
        assert dto.saved_time is None

    def test_from_dict_with_none_device_identifiers(self):
        """Test creating SessionDTO from dictionary with None device_identifiers."""
        data = {
            "cookies": {"session": "cookie_value"},
            "session_data": {"user": "test_user"},
            "hash": "test_hash",
            "user": "test_user",
            "device_identifiers": None,
            "saved_time": 1640995200,
        }

        dto = SessionDTO.from_dict(data)

        assert dto.cookies == {"session": "cookie_value"}
        assert dto.session_data == {"user": "test_user"}
        assert dto.hash == "test_hash"
        assert dto.user == "test_user"
        assert dto.device_identifiers is None
        assert dto.saved_time == 1640995200

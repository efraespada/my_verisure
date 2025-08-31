"""Unit tests for models."""

import pytest

from ...api.models.dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO
from ...api.models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
    ServiceDTO,
)
from ...api.models.dto.alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    DisarmResultDTO,
)
from ...api.models.dto.session_dto import SessionDTO, DeviceIdentifiersDTO

from ...api.models.domain.auth import Auth, AuthResult


class TestAuthDTO:
    """Test AuthDTO."""

    def test_from_dict(self):
        """Test creating AuthDTO from dictionary."""
        data = {
            "res": "OK",
            "msg": "Login successful",
            "hash": "test_hash",
            "refreshToken": "test_refresh",
            "lang": "es",
            "legals": True,
            "changePassword": False,
            "needDeviceAuthorization": True,
        }

        dto = AuthDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Login successful"
        assert dto.hash == "test_hash"
        assert dto.refresh_token == "test_refresh"
        assert dto.lang == "es"
        assert dto.legals is True
        assert dto.change_password is False
        assert dto.need_device_authorization is True

    def test_to_dict(self):
        """Test converting AuthDTO to dictionary."""
        dto = AuthDTO(
            res="OK",
            msg="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
            lang="es",
            legals=True,
            change_password=False,
            need_device_authorization=True,
        )

        result = dto.to_dict()

        assert result["res"] == "OK"
        assert result["msg"] == "Login successful"
        assert result["hash"] == "test_hash"
        assert result["refreshToken"] == "test_refresh"
        assert result["lang"] == "es"
        assert result["legals"] is True
        assert result["changePassword"] is False
        assert result["needDeviceAuthorization"] is True


class TestPhoneDTO:
    """Test PhoneDTO."""

    def test_phone_dto(self):
        """Test PhoneDTO creation."""
        dto = PhoneDTO(id=1, phone="+34600000000")

        assert dto.id == 1
        assert dto.phone == "+34600000000"


class TestOTPDataDTO:
    """Test OTPDataDTO."""

    def test_otp_data_dto(self):
        """Test OTPDataDTO creation."""
        phones = [PhoneDTO(id=1, phone="+34600000000")]
        dto = OTPDataDTO(
            phones=phones,
            otp_hash="test_hash",
            auth_code="10001",
            auth_type="OTP",
        )

        assert len(dto.phones) == 1
        assert dto.phones[0].id == 1
        assert dto.otp_hash == "test_hash"
        assert dto.auth_code == "10001"
        assert dto.auth_type == "OTP"


class TestInstallationDTO:
    """Test InstallationDTO."""

    def test_from_dict(self):
        """Test creating InstallationDTO from dictionary."""
        data = {
            "numinst": "12345",
            "alias": "Home",
            "panel": "PROTOCOL",
            "type": "ALARM",
            "name": "John",
            "surname": "Doe",
            "address": "123 Main St",
            "city": "Madrid",
            "postcode": "28001",
            "province": "Madrid",
            "email": "john@example.com",
            "phone": "+34600000000",
            "due": "2024-12-31",
            "role": "OWNER",
        }

        dto = InstallationDTO.from_dict(data)

        assert dto.numinst == "12345"
        assert dto.alias == "Home"
        assert dto.panel == "PROTOCOL"
        assert dto.type == "ALARM"
        assert dto.name == "John"
        assert dto.surname == "Doe"
        assert dto.address == "123 Main St"
        assert dto.city == "Madrid"
        assert dto.postcode == "28001"
        assert dto.province == "Madrid"
        assert dto.email == "john@example.com"
        assert dto.phone == "+34600000000"
        assert dto.due == "2024-12-31"
        assert dto.role == "OWNER"


class TestServiceDTO:
    """Test ServiceDTO."""

    def test_from_dict(self):
        """Test creating ServiceDTO from dictionary."""
        data = {
            "idService": "EST",
            "active": True,
            "visible": True,
            "bde": "test_bde",
            "isPremium": False,
            "codOper": "test_cod",
            "request": "EST",
            "minWrapperVersion": "1.0.0",
            "unprotectActive": False,
            "unprotectDeviceStatus": False,
            "instDate": "2024-01-01",
            "genericConfig": {"total": 1},
            "attributes": {"test": "value"},
        }

        dto = ServiceDTO.from_dict(data)

        assert dto.id_service == "EST"
        assert dto.active is True
        assert dto.visible is True
        assert dto.bde == "test_bde"
        assert dto.is_premium is False
        assert dto.cod_oper == "test_cod"
        assert dto.request == "EST"
        assert dto.min_wrapper_version == "1.0.0"
        assert dto.unprotect_active is False
        assert dto.unprotect_device_status is False
        assert dto.inst_date == "2024-01-01"
        assert dto.generic_config == {"total": 1}
        assert dto.attributes == {"test": "value"}


class TestInstallationServicesDTO:
    """Test InstallationServicesDTO."""

    def test_from_dict_with_services(self):
        """Test creating InstallationServicesDTO from dictionary with services."""
        data = {
            "res": "OK",
            "msg": "Success",
            "language": "es",
            "installation": {
                "services": [
                    {"idService": "EST", "active": True, "visible": True}
                ]
            },
        }

        dto = InstallationServicesDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Success"
        assert dto.language == "es"
        assert len(dto.services) == 1
        assert dto.services[0].id_service == "EST"
        assert dto.services[0].active is True

    def test_from_dict_without_services(self):
        """Test creating InstallationServicesDTO from dictionary without services."""
        data = {"res": "OK", "msg": "Success", "language": "es"}

        dto = InstallationServicesDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Success"
        assert dto.language == "es"
        assert len(dto.services) == 0


class TestAlarmStatusDTO:
    """Test AlarmStatusDTO."""

    def test_from_dict(self):
        """Test creating AlarmStatusDTO from dictionary."""
        data = {
            "res": "OK",
            "msg": "Alarm status retrieved",
            "status": "DISARMED",
            "numinst": "12345",
            "protomResponse": "test_response",
            "protomResponseDate": "2024-01-01T00:00:00Z",
            "forcedArmed": False,
        }

        dto = AlarmStatusDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Alarm status retrieved"
        assert dto.status == "DISARMED"
        assert dto.numinst == "12345"
        assert dto.protom_response == "test_response"
        assert dto.protom_response_date == "2024-01-01T00:00:00Z"
        assert dto.forced_armed is False


class TestArmResultDTO:
    """Test ArmResultDTO."""

    def test_from_dict(self):
        """Test creating ArmResultDTO from dictionary."""
        data = {
            "res": "OK",
            "msg": "Arm command sent",
            "referenceId": "ref_123",
        }

        dto = ArmResultDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Arm command sent"
        assert dto.reference_id == "ref_123"


class TestDisarmResultDTO:
    """Test DisarmResultDTO."""

    def test_from_dict(self):
        """Test creating DisarmResultDTO from dictionary."""
        data = {
            "res": "OK",
            "msg": "Disarm command sent",
            "referenceId": "ref_456",
        }

        dto = DisarmResultDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Disarm command sent"
        assert dto.reference_id == "ref_456"


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


class TestDomainModels:
    """Test domain models."""

    def test_auth_validation(self):
        """Test Auth domain model validation."""
        # Valid auth
        auth = Auth(username="test_user", password="test_pass")
        assert auth.username == "test_user"
        assert auth.password == "test_pass"

        # Invalid auth - missing username
        with pytest.raises(ValueError, match="Username is required"):
            Auth(username="", password="test_pass")

        # Invalid auth - missing password
        with pytest.raises(ValueError, match="Password is required"):
            Auth(username="test_user", password="")

    def test_auth_result_from_dto(self):
        """Test AuthResult from DTO."""
        dto = AuthDTO(
            res="OK",
            msg="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
            lang="es",
            legals=True,
            change_password=False,
            need_device_authorization=True,
        )

        result = AuthResult.from_dto(dto)

        assert result.success is True
        assert result.message == "Login successful"
        assert result.hash == "test_hash"
        assert result.refresh_token == "test_refresh"
        assert result.lang == "es"
        assert result.legals is True
        assert result.change_password is False
        assert result.need_device_authorization is True

    def test_auth_result_to_dto(self):
        """Test AuthResult to DTO."""
        result = AuthResult(
            success=True,
            message="Login successful",
            hash="test_hash",
            refresh_token="test_refresh",
            lang="es",
            legals=True,
            change_password=False,
            need_device_authorization=True,
        )

        dto = result.to_dto()

        assert dto.res == "OK"
        assert dto.msg == "Login successful"
        assert dto.hash == "test_hash"
        assert dto.refresh_token == "test_refresh"
        assert dto.lang == "es"
        assert dto.legals is True
        assert dto.change_password is False
        assert dto.need_device_authorization is True

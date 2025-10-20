"""Unit tests for AuthDTO and related DTOs."""

import pytest

from ...api.models.dto.auth_dto import AuthDTO, OTPDataDTO, PhoneDTO


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

    def test_from_dict_with_missing_fields(self):
        """Test creating AuthDTO from dictionary with missing fields."""
        data = {
            "res": "OK",
            "msg": "Login successful",
        }

        dto = AuthDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Login successful"
        assert dto.hash is None
        assert dto.refresh_token is None
        assert dto.lang is None
        assert dto.legals is None
        assert dto.change_password is None
        assert dto.need_device_authorization is None


class TestPhoneDTO:
    """Test PhoneDTO."""

    def test_phone_dto_creation(self):
        """Test PhoneDTO creation."""
        dto = PhoneDTO(id=1, phone="+34600000000")

        assert dto.id == 1
        assert dto.phone == "+34600000000"

    def test_phone_dto_from_dict(self):
        """Test PhoneDTO from dictionary."""
        data = {"id": 2, "phone": "+34600000001"}
        dto = PhoneDTO.from_dict(data)

        assert dto.id == 2
        assert dto.phone == "+34600000001"

    def test_phone_dto_to_dict(self):
        """Test PhoneDTO to dictionary."""
        dto = PhoneDTO(id=3, phone="+34600000002")
        result = dto.to_dict()

        assert result["id"] == 3
        assert result["phone"] == "+34600000002"


class TestOTPDataDTO:
    """Test OTPDataDTO."""

    def test_otp_data_dto_creation(self):
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

    def test_otp_data_dto_from_dict(self):
        """Test OTPDataDTO from dictionary."""
        data = {
            "phones": [{"id": 1, "phone": "+34600000000"}],
            "otpHash": "test_hash",
            "authCode": "10001",
            "authType": "OTP",
        }

        dto = OTPDataDTO.from_dict(data)

        assert len(dto.phones) == 1
        assert dto.phones[0].id == 1
        assert dto.phones[0].phone == "+34600000000"
        assert dto.otp_hash == "test_hash"
        assert dto.auth_code == "10001"
        assert dto.auth_type == "OTP"

    def test_otp_data_dto_to_dict(self):
        """Test OTPDataDTO to dictionary."""
        phones = [PhoneDTO(id=1, phone="+34600000000")]
        dto = OTPDataDTO(
            phones=phones,
            otp_hash="test_hash",
            auth_code="10001",
            auth_type="OTP",
        )

        result = dto.to_dict()

        assert result["phones"][0]["id"] == 1
        assert result["phones"][0]["phone"] == "+34600000000"
        assert result["otpHash"] == "test_hash"
        assert result["authCode"] == "10001"
        assert result["authType"] == "OTP"

"""Unit tests for AlarmDTO and related DTOs."""

import pytest

from ...api.models.dto.alarm_dto import (
    AlarmStatusDTO,
    ArmResultDTO,
    DisarmResultDTO,
)


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

    def test_to_dict(self):
        """Test converting AlarmStatusDTO to dictionary."""
        dto = AlarmStatusDTO(
            res="OK",
            msg="Alarm status retrieved",
            status="DISARMED",
            numinst="12345",
            protom_response="test_response",
            protom_response_date="2024-01-01T00:00:00Z",
            forced_armed=False,
        )

        result = dto.to_dict()

        assert result["res"] == "OK"
        assert result["msg"] == "Alarm status retrieved"
        assert result["status"] == "DISARMED"
        assert result["numinst"] == "12345"
        assert result["protomResponse"] == "test_response"
        assert result["protomResponseDate"] == "2024-01-01T00:00:00Z"
        assert result["forcedArmed"] is False

    def test_from_dict_with_missing_fields(self):
        """Test creating AlarmStatusDTO from dictionary with missing fields."""
        data = {
            "res": "OK",
            "msg": "Alarm status retrieved",
        }

        dto = AlarmStatusDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg == "Alarm status retrieved"
        assert dto.status is None
        assert dto.numinst is None
        assert dto.protom_response is None
        assert dto.protom_response_date is None
        assert dto.forced_armed is None


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

    def test_to_dict(self):
        """Test converting ArmResultDTO to dictionary."""
        dto = ArmResultDTO(
            res="OK",
            msg="Arm command sent",
            reference_id="ref_123",
        )

        result = dto.to_dict()

        assert result["res"] == "OK"
        assert result["msg"] == "Arm command sent"
        assert result["referenceId"] == "ref_123"

    def test_from_dict_with_missing_fields(self):
        """Test creating ArmResultDTO from dictionary with missing fields."""
        data = {
            "res": "OK",
        }

        dto = ArmResultDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg is None
        assert dto.reference_id is None


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

    def test_to_dict(self):
        """Test converting DisarmResultDTO to dictionary."""
        dto = DisarmResultDTO(
            res="OK",
            msg="Disarm command sent",
            reference_id="ref_456",
        )

        result = dto.to_dict()

        assert result["res"] == "OK"
        assert result["msg"] == "Disarm command sent"
        assert result["referenceId"] == "ref_456"

    def test_from_dict_with_missing_fields(self):
        """Test creating DisarmResultDTO from dictionary with missing fields."""
        data = {
            "res": "OK",
        }

        dto = DisarmResultDTO.from_dict(data)

        assert dto.res == "OK"
        assert dto.msg is None
        assert dto.reference_id is None

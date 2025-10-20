"""Unit tests for InstallationDTO and related DTOs."""

import pytest

from ...api.models.dto.installation_dto import (
    InstallationDTO,
    DetailedInstallationDTO,
    ServiceDTO,
)


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

    def test_to_dict(self):
        """Test converting InstallationDTO to dictionary."""
        dto = InstallationDTO(
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
            due="2024-12-31",
            role="OWNER",
        )

        result = dto.to_dict()

        assert result["numinst"] == "12345"
        assert result["alias"] == "Home"
        assert result["panel"] == "PROTOCOL"
        assert result["type"] == "ALARM"
        assert result["name"] == "John"
        assert result["surname"] == "Doe"
        assert result["address"] == "123 Main St"
        assert result["city"] == "Madrid"
        assert result["postcode"] == "28001"
        assert result["province"] == "Madrid"
        assert result["email"] == "john@example.com"
        assert result["phone"] == "+34600000000"
        assert result["due"] == "2024-12-31"
        assert result["role"] == "OWNER"

    def test_from_dict_with_missing_fields(self):
        """Test creating InstallationDTO from dictionary with missing fields."""
        data = {
            "numinst": "12345",
            "alias": "Home",
        }

        dto = InstallationDTO.from_dict(data)

        assert dto.numinst == "12345"
        assert dto.alias == "Home"
        assert dto.panel is None
        assert dto.type is None
        assert dto.name is None
        assert dto.surname is None


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

    def test_to_dict(self):
        """Test converting ServiceDTO to dictionary."""
        dto = ServiceDTO(
            id_service="EST",
            active=True,
            visible=True,
            bde="test_bde",
            is_premium=False,
            cod_oper="test_cod",
            request="EST",
            min_wrapper_version="1.0.0",
            unprotect_active=False,
            unprotect_device_status=False,
            inst_date="2024-01-01",
            generic_config={"total": 1},
            attributes={"test": "value"},
        )

        result = dto.to_dict()

        assert result["idService"] == "EST"
        assert result["active"] is True
        assert result["visible"] is True
        assert result["bde"] == "test_bde"
        assert result["isPremium"] is False
        assert result["codOper"] == "test_cod"
        assert result["request"] == "EST"
        assert result["minWrapperVersion"] == "1.0.0"
        assert result["unprotectActive"] is False
        assert result["unprotectDeviceStatus"] is False
        assert result["instDate"] == "2024-01-01"
        assert result["genericConfig"] == {"total": 1}
        assert result["attributes"] == {"test": "value"}


class TestDetailedInstallationDTO:
    """Test DetailedInstallationDTO."""

    def test_from_dict_with_services(self):
        """Test creating DetailedInstallationDTO from dictionary with services."""
        data = {
            "language": "es",
            "installation": {
                "numinst": "6220569",
                "role": "OWNER",
                "alias": "Test Installation",
                "status": "OP",
                "panel": "SDVFAST",
                "sim": "123456789",
                "instIbs": "16824809",
                "services": [
                    {"idService": "EST", "active": True, "visible": True}
                ],
                "configRepoUser": None,
                "capabilities": "test_capabilities"
            },
        }

        dto = DetailedInstallationDTO.from_dict(data)

        assert dto.language == "es"
        assert dto.installation.numinst == "6220569"
        assert dto.installation.role == "OWNER"
        assert dto.installation.alias == "Test Installation"
        assert dto.installation.status == "OP"
        assert dto.installation.panel == "SDVFAST"
        assert dto.installation.sim == "123456789"
        assert dto.installation.instIbs == "16824809"
        assert len(dto.installation.services) == 1
        assert dto.installation.services[0].id_service == "EST"
        assert dto.installation.services[0].active is True
        assert dto.installation.capabilities == "test_capabilities"

    def test_from_dict_without_services(self):
        """Test creating DetailedInstallationDTO from dictionary without services."""
        data = {
            "language": "es",
            "installation": {
                "numinst": "6220569",
                "role": "OWNER",
                "alias": "Test Installation",
                "status": "OP",
                "panel": "SDVFAST",
                "sim": "123456789",
                "instIbs": "16824809",
                "services": [],
                "configRepoUser": None,
                "capabilities": None
            },
        }

        dto = DetailedInstallationDTO.from_dict(data)

        assert dto.language == "es"
        assert dto.installation.numinst == "6220569"
        assert dto.installation.role == "OWNER"
        assert dto.installation.alias == "Test Installation"
        assert dto.installation.status == "OP"
        assert dto.installation.panel == "SDVFAST"
        assert dto.installation.sim == "123456789"
        assert dto.installation.instIbs == "16824809"
        assert len(dto.installation.services) == 0
        assert dto.installation.capabilities is None

    def test_to_dict(self):
        """Test converting DetailedInstallationDTO to dictionary."""
        from ...api.models.dto.installation_dto import InstallationDataDTO
        
        installation_data = InstallationDataDTO(
            numinst="6220569",
            role="OWNER",
            alias="Test Installation",
            status="OP",
            panel="SDVFAST",
            sim="123456789",
            instIbs="16824809",
            services=[],
            configRepoUser=None,
            capabilities="test_capabilities"
        )
        
        dto = DetailedInstallationDTO(
            language="es",
            installation=installation_data
        )

        result = dto.to_dict()

        assert result["language"] == "es"
        assert result["installation"]["numinst"] == "6220569"
        assert result["installation"]["role"] == "OWNER"
        assert result["installation"]["alias"] == "Test Installation"

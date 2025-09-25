#!/usr/bin/env python3
"""
Unit tests for InstallationRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock

# Add the package root to the path
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from core.repositories.implementations.installation_repository_impl import (
    InstallationRepositoryImpl,
)
from core.repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from core.api.exceptions import MyVerisureError
from core.api.models.dto.installation_dto import (
    InstallationDTO,
    InstallationServicesDTO,
    ServiceDTO,
)


class TestInstallationRepository:
    """Test cases for InstallationRepository implementation."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock MyVerisureClient."""
        mock_client = Mock()
        mock_client.get_installations = AsyncMock()
        mock_client.get_installation_services = AsyncMock()
        # Mock the hash token
        mock_client._hash = "test_hash_token_12345"
        return mock_client

    @pytest.fixture
    def installation_repository(self, mock_client):
        """Create InstallationRepository instance with mocked client."""
        repo = InstallationRepositoryImpl(client=mock_client)
        # Clear cache before each test
        repo._clear_cache()
        return repo

    def test_installation_repository_implements_interface(
        self, installation_repository
    ):
        """Test that InstallationRepositoryImpl implements InstallationRepository interface."""
        assert isinstance(installation_repository, InstallationRepository)

    @pytest.mark.asyncio
    async def test_get_installations_success(
        self, installation_repository, mock_client
    ):
        """Test successful get installations."""
        # Arrange
        expected_installations_data = [
            InstallationDTO(
                numinst="12345",
                alias="Home",
                panel="panel1",
                type="residential",
                name="John",
                surname="Doe",
                address="123 Main St",
                city="Madrid",
                postcode="28001",
                province="Madrid",
                email="john@example.com",
                phone="+34600000000",
                due="2024-12-31",
                role="owner",
            ),
            InstallationDTO(
                numinst="67890",
                alias="Office",
                panel="panel2",
                type="commercial",
                name="Jane",
                surname="Smith",
                address="456 Business Ave",
                city="Barcelona",
                postcode="08001",
                province="Barcelona",
                email="jane@example.com",
                phone="+34600000001",
                due="2024-12-31",
                role="user",
            ),
        ]

        mock_client.get_installations.return_value = (
            expected_installations_data
        )

        # Act
        result = await installation_repository.get_installations()

        # Assert
        assert len(result) == 2
        assert result[0].numinst == "12345"
        assert result[0].alias == "Home"
        assert result[0].type == "residential"
        assert result[1].numinst == "67890"
        assert result[1].alias == "Office"
        assert result[1].type == "commercial"
        mock_client.get_installations.assert_called_once_with(
            hash_token="test_hash_token_12345", session_data=mock_client._session_data
        )

    @pytest.mark.asyncio
    async def test_get_installations_empty(
        self, installation_repository, mock_client
    ):
        """Test get installations returns empty list."""
        # Arrange
        mock_client.get_installations.return_value = []

        # Act
        result = await installation_repository.get_installations()

        # Assert
        assert result == []
        mock_client.get_installations.assert_called_once_with(
            hash_token="test_hash_token_12345", session_data=mock_client._session_data
        )

    @pytest.mark.asyncio
    async def test_get_installations_raises_exception(
        self, installation_repository, mock_client
    ):
        """Test get installations raises exception."""
        # Arrange
        mock_client.get_installations.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await installation_repository.get_installations()

    @pytest.mark.asyncio
    async def test_get_installation_services_success(
        self, installation_repository, mock_client
    ):
        """Test successful get installation services."""
        # Arrange
        installation_id = "12345"
        expected_services_data = InstallationServicesDTO(
            installation={
                "numinst": "12345",
                "role": "owner",
                "alias": "Home",
                "status": "active",
                "panel": "panel1",
                "sim": "sim1",
                "instIbs": "ibs1",
            },
            services=[
                ServiceDTO(
                    id_service="EST",
                    active=True,
                    visible=True,
                    bde=False,
                    is_premium=False,
                    cod_oper="EST",
                    request="EST",
                    min_wrapper_version="1.0",
                    unprotect_active=False,
                    unprotect_device_status=False,
                    inst_date="2024-01-01",
                    generic_config={},
                    attributes=[],
                ),
                ServiceDTO(
                    id_service="CAM",
                    active=True,
                    visible=True,
                    bde=True,
                    is_premium=True,
                    cod_oper="CAM",
                    request="CAM",
                    min_wrapper_version="1.0",
                    unprotect_active=False,
                    unprotect_device_status=False,
                    inst_date="2024-01-01",
                    generic_config={},
                    attributes=[],
                ),
            ],
            language="es",
        )

        mock_client.get_installation_services.return_value = (
            expected_services_data
        )

        # Act
        result = await installation_repository.get_installation_services(
            installation_id
        )

        # Assert
        assert result.language == "es"
        assert len(result.services) == 2
        assert result.services[0].id_service == "EST"
        assert result.services[0].active is True
        assert result.services[1].id_service == "CAM"
        assert result.services[1].active is True
        assert result.installation_data["status"] == "active"
        assert result.installation_data["panel"] == "panel1"
        mock_client.get_installation_services.assert_called_once_with(
            installation_id, False, hash_token="test_hash_token_12345", session_data=mock_client._session_data
        )

    @pytest.mark.asyncio
    async def test_get_installation_services_failure(
        self, installation_repository, mock_client
    ):
        """Test failed get installation services."""
        # Arrange
        installation_id = "12345"
        mock_client.get_installation_services.side_effect = MyVerisureError(
            "Installation not found"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Installation not found"):
            await installation_repository.get_installation_services(
                installation_id
            )

    @pytest.mark.asyncio
    async def test_get_installation_services_raises_exception(
        self, installation_repository, mock_client
    ):
        """Test get installation services raises exception."""
        # Arrange
        installation_id = "12345"
        mock_client.get_installation_services.side_effect = MyVerisureError(
            "Connection failed"
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await installation_repository.get_installation_services(
                installation_id
            )


if __name__ == "__main__":
    pytest.main([__file__])

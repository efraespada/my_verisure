#!/usr/bin/env python3
"""
Unit tests for InstallationUseCase implementation.
"""

import os
import sys
import pytest
from unittest.mock import Mock, AsyncMock

# Add the package root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from use_cases.implementations.installation_use_case_impl import (
    InstallationUseCaseImpl,
)
from use_cases.interfaces.installation_use_case import InstallationUseCase
from repositories.interfaces.installation_repository import (
    InstallationRepository,
)
from api.models.domain.installation import Installation, InstallationServices
from api.models.domain.service import Service
from api.exceptions import MyVerisureError


class TestInstallationUseCase:
    """Test cases for InstallationUseCase implementation."""

    @pytest.fixture
    def mock_installation_repository(self):
        """Create a mock installation repository."""
        mock_repo = Mock(spec=InstallationRepository)
        mock_repo.get_installations = AsyncMock()
        mock_repo.get_installation_services = AsyncMock()
        return mock_repo

    @pytest.fixture
    def installation_use_case(self, mock_installation_repository):
        """Create InstallationUseCase instance with mocked dependencies."""
        return InstallationUseCaseImpl(
            installation_repository=mock_installation_repository
        )

    def test_installation_use_case_implements_interface(
        self, installation_use_case
    ):
        """Test InstallationUseCaseImpl implements InstallationUseCase interface."""
        assert isinstance(installation_use_case, InstallationUseCase)

    @pytest.mark.asyncio
    async def test_get_installations_success(
        self, installation_use_case, mock_installation_repository
    ):
        """Test successful get installations."""
        # Arrange
        expected_installations = [
            Installation(
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
            Installation(
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

        mock_installation_repository.get_installations.return_value = (
            expected_installations
        )

        # Act
        result = await installation_use_case.get_installations()

        # Assert
        assert len(result) == 2
        assert result[0].numinst == "12345"
        assert result[0].alias == "Home"
        assert result[1].numinst == "67890"
        assert result[1].alias == "Office"
        mock_installation_repository.get_installations.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_installations_empty(
        self, installation_use_case, mock_installation_repository
    ):
        """Test get installations returns empty list."""
        # Arrange
        mock_installation_repository.get_installations.return_value = []

        # Act
        result = await installation_use_case.get_installations()

        # Assert
        assert result == []
        mock_installation_repository.get_installations.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_installations_raises_exception(
        self, installation_use_case, mock_installation_repository
    ):
        """Test get installations raises exception."""
        # Arrange
        mock_installation_repository.get_installations.side_effect = (
            MyVerisureError("Connection failed")
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await installation_use_case.get_installations()

    @pytest.mark.asyncio
    async def test_get_installation_services_success(
        self, installation_use_case, mock_installation_repository
    ):
        """Test successful get installation services."""
        # Arrange
        installation_id = "12345"
        expected_services = [
            Service(
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
            Service(
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
        ]

        expected_result = InstallationServices(
            success=True,
            services=expected_services,
            installation_data={
                "status": "active",
                "panel": "panel1",
                "sim": "sim1",
                "instIbs": "ibs1",
                "role": "owner",
            },
            message="Services retrieved successfully",
        )

        mock_installation_repository.get_installation_services.return_value = (
            expected_result
        )

        # Act
        result = await installation_use_case.get_installation_services(
            installation_id
        )

        # Assert
        assert result.success is True
        assert len(result.services) == 2
        assert result.services[0].id_service == "EST"
        assert result.services[1].id_service == "CAM"
        assert result.installation_data["status"] == "active"
        assert result.message == "Services retrieved successfully"
        mock_installation_repository.get_installation_services.assert_called_once_with(
            installation_id, False
        )

    @pytest.mark.asyncio
    async def test_get_installation_services_failure(
        self, installation_use_case, mock_installation_repository
    ):
        """Test failed get installation services."""
        # Arrange
        installation_id = "12345"
        expected_result = InstallationServices(
            success=False,
            services=[],
            installation_data={},
            message="Installation not found",
        )

        mock_installation_repository.get_installation_services.return_value = (
            expected_result
        )

        # Act
        result = await installation_use_case.get_installation_services(
            installation_id
        )

        # Assert
        assert result.success is False
        assert len(result.services) == 0
        assert result.message == "Installation not found"
        mock_installation_repository.get_installation_services.assert_called_once_with(
            installation_id, False
        )

    @pytest.mark.asyncio
    async def test_get_installation_services_raises_exception(
        self, installation_use_case, mock_installation_repository
    ):
        """Test get installation services raises exception."""
        # Arrange
        installation_id = "12345"
        mock_installation_repository.get_installation_services.side_effect = (
            MyVerisureError("Connection failed")
        )

        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await installation_use_case.get_installation_services(
                installation_id
            )

    @pytest.mark.asyncio
    async def test_get_installation_services_with_cache(
        self, installation_use_case, mock_installation_repository
    ):
        """Test that installation services are retrieved correctly (cache handled by repository)."""
        # Arrange
        installation_id = "12345"
        expected_services = InstallationServices(
            success=True,
            message="Services retrieved successfully",
            installation_data={"panel": "PROTOCOL"},
            capabilities="test_capabilities",
        )

        mock_installation_repository.get_installation_services.return_value = (
            expected_services
        )

        # Act - First call
        result1 = await installation_use_case.get_installation_services(
            installation_id
        )

        # Act - Second call (cache is handled by repository)
        result2 = await installation_use_case.get_installation_services(
            installation_id
        )

        # Assert
        assert result1.success is True
        assert result2.success is True
        assert result1.installation_data["panel"] == "PROTOCOL"
        assert result2.installation_data["panel"] == "PROTOCOL"

        # Repository should be called twice (cache is handled internally by repository)
        assert (
            mock_installation_repository.get_installation_services.call_count
            == 2
        )
        mock_installation_repository.get_installation_services.assert_any_call(
            installation_id, False
        )

    @pytest.mark.asyncio
    async def test_get_installation_services_force_refresh(
        self, installation_use_case, mock_installation_repository
    ):
        """Test that force_refresh bypasses cache."""
        # Arrange
        installation_id = "12345"
        expected_services = InstallationServices(
            success=True,
            message="Services retrieved successfully",
            installation_data={"panel": "PROTOCOL"},
            capabilities="test_capabilities",
        )

        mock_installation_repository.get_installation_services.return_value = (
            expected_services
        )

        # Act - First call
        result1 = await installation_use_case.get_installation_services(
            installation_id
        )

        # Act - Second call with force_refresh=True
        result2 = await installation_use_case.get_installation_services(
            installation_id, force_refresh=True
        )

        # Assert
        assert result1.success is True
        assert result2.success is True

        # Repository should be called twice (once for each request due to force_refresh)
        assert (
            mock_installation_repository.get_installation_services.call_count
            == 2
        )
        mock_installation_repository.get_installation_services.assert_any_call(
            installation_id, False
        )
        mock_installation_repository.get_installation_services.assert_any_call(
            installation_id, True
        )




if __name__ == "__main__":
    pytest.main([__file__])

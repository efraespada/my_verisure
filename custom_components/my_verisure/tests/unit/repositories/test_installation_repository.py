#!/usr/bin/env python3
"""
Unit tests for InstallationRepository implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Optional, List, Dict, Any

# Add the package root to the path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

from repositories.implementations.installation_repository_impl import InstallationRepositoryImpl
from repositories.interfaces.installation_repository import InstallationRepository
from api.models.domain.installation import Installation, InstallationServices
from api.models.domain.service import Service
from api.models.dto.installation_dto import InstallationDTO
from api.models.dto.service_dto import ServiceDTO
from api.exceptions import MyVerisureError


class TestInstallationRepository:
    """Test cases for InstallationRepository implementation."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock MyVerisureClient."""
        mock_client = Mock()
        mock_client.get_installations = AsyncMock()
        mock_client.get_installation_services = AsyncMock()
        return mock_client
    
    @pytest.fixture
    def installation_repository(self, mock_client):
        """Create InstallationRepository instance with mocked client."""
        return InstallationRepositoryImpl(client=mock_client)
    
    def test_installation_repository_implements_interface(self, installation_repository):
        """Test that InstallationRepositoryImpl implements InstallationRepository interface."""
        assert isinstance(installation_repository, InstallationRepository)
    
    @pytest.mark.asyncio
    async def test_get_installations_success(self, installation_repository, mock_client):
        """Test successful get installations."""
        # Arrange
        expected_installations_data = [
            {
                "numinst": "12345",
                "alias": "Home",
                "panel": "panel1",
                "type": "residential",
                "name": "John",
                "surname": "Doe",
                "address": "123 Main St",
                "city": "Madrid",
                "postcode": "28001",
                "province": "Madrid",
                "email": "john@example.com",
                "phone": "+34600000000",
                "due": "2024-12-31",
                "role": "owner"
            },
            {
                "numinst": "67890",
                "alias": "Office",
                "panel": "panel2",
                "type": "commercial",
                "name": "Jane",
                "surname": "Smith",
                "address": "456 Business Ave",
                "city": "Barcelona",
                "postcode": "08001",
                "province": "Barcelona",
                "email": "jane@example.com",
                "phone": "+34600000001",
                "due": "2024-12-31",
                "role": "user"
            }
        ]
        
        mock_client.get_installations.return_value = expected_installations_data
        
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
        mock_client.get_installations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_installations_empty(self, installation_repository, mock_client):
        """Test get installations returns empty list."""
        # Arrange
        mock_client.get_installations.return_value = []
        
        # Act
        result = await installation_repository.get_installations()
        
        # Assert
        assert result == []
        mock_client.get_installations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_installations_raises_exception(self, installation_repository, mock_client):
        """Test get installations raises exception."""
        # Arrange
        mock_client.get_installations.side_effect = MyVerisureError("Connection failed")
        
        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await installation_repository.get_installations()
    
    @pytest.mark.asyncio
    async def test_get_installation_services_success(self, installation_repository, mock_client):
        """Test successful get installation services."""
        # Arrange
        installation_id = "12345"
        expected_services_data = {
            "res": "OK",  # This is required for success=True
            "msg": "Services retrieved successfully",
            "language": "es",
            "installation": {
                "numinst": "12345",
                "role": "owner",
                "alias": "Home",
                "status": "active",
                "panel": "panel1",
                "sim": "sim1",
                "instIbs": "ibs1",
                "services": [
                    {
                        "idService": "EST",
                        "active": True,
                        "visible": True,
                        "bde": False,
                        "isPremium": False,
                        "codOper": "EST",
                        "request": "EST",
                        "minWrapperVersion": "1.0",
                        "unprotectActive": False,
                        "unprotectDeviceStatus": False,
                        "instDate": "2024-01-01",
                        "genericConfig": {},
                        "attributes": []
                    },
                    {
                        "idService": "CAM",
                        "active": True,
                        "visible": True,
                        "bde": True,
                        "isPremium": True,
                        "codOper": "CAM",
                        "request": "CAM",
                        "minWrapperVersion": "1.0",
                        "unprotectActive": False,
                        "unprotectDeviceStatus": False,
                        "instDate": "2024-01-01",
                        "genericConfig": {},
                        "attributes": []
                    }
                ]
            }
        }
        
        mock_client.get_installation_services.return_value = expected_services_data
        
        # Act
        result = await installation_repository.get_installation_services(installation_id)
        
        # Assert
        assert result.success is True
        assert len(result.services) == 2
        assert result.services[0].id_service == "EST"
        assert result.services[0].active is True
        assert result.services[1].id_service == "CAM"
        assert result.services[1].active is True
        assert result.installation_data["status"] == "active"
        assert result.installation_data["panel"] == "panel1"
        assert result.message == "Services retrieved successfully"
        mock_client.get_installation_services.assert_called_once_with(installation_id, False)
    
    @pytest.mark.asyncio
    async def test_get_installation_services_failure(self, installation_repository, mock_client):
        """Test failed get installation services."""
        # Arrange
        installation_id = "12345"
        mock_client.get_installation_services.side_effect = MyVerisureError("Installation not found")
        
        # Act & Assert
        with pytest.raises(MyVerisureError, match="Installation not found"):
            await installation_repository.get_installation_services(installation_id)
    
    @pytest.mark.asyncio
    async def test_get_installation_services_raises_exception(self, installation_repository, mock_client):
        """Test get installation services raises exception."""
        # Arrange
        installation_id = "12345"
        mock_client.get_installation_services.side_effect = MyVerisureError("Connection failed")
        
        # Act & Assert
        with pytest.raises(MyVerisureError, match="Connection failed"):
            await installation_repository.get_installation_services(installation_id)


if __name__ == "__main__":
    pytest.main([__file__]) 
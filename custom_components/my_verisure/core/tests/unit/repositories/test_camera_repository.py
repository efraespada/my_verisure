#!/usr/bin/env python3
"""
Unit tests for CameraRepository implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from ....repositories.implementations.camera_repository_impl import (
    CameraRepositoryImpl,
)
from ....repositories.interfaces.camera_repository import CameraRepository
from ....api.models.domain.camera_request_image import CameraRequestImageResult
from ....api.exceptions import MyVerisureError


class TestCameraRepository:
    """Test cases for CameraRepository implementation."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock CameraClient."""
        mock_client = Mock()
        mock_client.request_image = AsyncMock()
        mock_client.get_images = AsyncMock()
        return mock_client

    @pytest.fixture
    def camera_repository(self, mock_client):
        """Create CameraRepository instance with mocked client."""
        return CameraRepositoryImpl(client=mock_client)

    def test_camera_repository_implements_interface(self, camera_repository):
        """Test that CameraRepositoryImpl implements CameraRepository interface."""
        assert isinstance(camera_repository, CameraRepository)

    @pytest.mark.asyncio
    async def test_request_image_success(self, camera_repository, mock_client):
        """Test successful camera image request."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        devices = [1, 2, 3]
        capabilities = "test_capabilities"
        
        # Mock DTO response
        mock_dto = Mock()
        mock_dto.success = True
        mock_dto.successful_requests = 3
        mock_dto.reference_id = "ref_123"
        
        mock_client.request_image.return_value = mock_dto
        
        # Mock the from_dto method
        expected_result = CameraRequestImageResult(
            success=True,
            successful_requests=3,
            reference_id="ref_123"
        )
        
        with patch('core.api.models.domain.camera_request_image.CameraRequestImageResult.from_dto') as mock_from_dto:
            mock_from_dto.return_value = expected_result
            
            # Act
            result = await camera_repository.request_image(
                installation_id, panel, devices, capabilities
            )
            
            # Assert
            assert result == expected_result
            mock_client.request_image.assert_called_once_with(
                installation_id=installation_id,
                panel=panel,
                devices=devices,
                capabilities=capabilities,
            )
            mock_from_dto.assert_called_once_with(mock_dto)

    @pytest.mark.asyncio
    async def test_request_image_failure(self, camera_repository, mock_client):
        """Test failed camera image request."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        devices = [1, 2, 3]
        capabilities = "test_capabilities"
        
        mock_client.request_image.side_effect = Exception("Connection failed")
        
        # Act
        result = await camera_repository.request_image(
            installation_id, panel, devices, capabilities
        )
        
        # Assert
        assert result.success is False
        assert result.successful_requests == 0
        assert result.reference_id is None
        mock_client.request_image.assert_called_once_with(
            installation_id=installation_id,
            panel=panel,
            devices=devices,
            capabilities=capabilities,
        )

    @pytest.mark.asyncio
    async def test_request_image_raises_exception(self, camera_repository, mock_client):
        """Test camera image request raises exception."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        devices = [1, 2, 3]
        capabilities = "test_capabilities"
        
        mock_client.request_image.side_effect = MyVerisureError("API error")
        
        # Act
        result = await camera_repository.request_image(
            installation_id, panel, devices, capabilities
        )
        
        # Assert
        assert result.success is False
        assert result.successful_requests == 0
        assert result.reference_id is None

    @pytest.mark.asyncio
    async def test_get_images_success(self, camera_repository, mock_client):
        """Test successful get camera images."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        device = "device1"
        zone_id = "zone1"
        capabilities = "test_capabilities"
        
        expected_images = {
            "success": True,
            "images": [
                {"id": "img1", "url": "http://example.com/img1.jpg"},
                {"id": "img2", "url": "http://example.com/img2.jpg"}
            ],
            "count": 2
        }
        
        mock_client.get_images.return_value = expected_images
        
        # Act
        result = await camera_repository.get_images(
            installation_id, panel, device, zone_id, capabilities
        )
        
        # Assert
        assert result == expected_images
        mock_client.get_images.assert_called_once_with(
            installation_id=installation_id,
            panel=panel,
            device=device,
            zone_id=zone_id,
            capabilities=capabilities,
        )

    @pytest.mark.asyncio
    async def test_get_images_failure(self, camera_repository, mock_client):
        """Test failed get camera images."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        device = "device1"
        zone_id = "zone1"
        capabilities = "test_capabilities"
        
        mock_client.get_images.side_effect = Exception("Connection failed")
        
        # Act
        result = await camera_repository.get_images(
            installation_id, panel, device, zone_id, capabilities
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Connection failed" in result["error"]
        assert "Camera images retrieval failed" in result["message"]
        mock_client.get_images.assert_called_once_with(
            installation_id=installation_id,
            panel=panel,
            device=device,
            zone_id=zone_id,
            capabilities=capabilities,
        )

    @pytest.mark.asyncio
    async def test_get_images_raises_exception(self, camera_repository, mock_client):
        """Test get camera images raises exception."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        device = "device1"
        zone_id = "zone1"
        capabilities = "test_capabilities"
        
        mock_client.get_images.side_effect = MyVerisureError("API error")
        
        # Act
        result = await camera_repository.get_images(
            installation_id, panel, device, zone_id, capabilities
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "API error" in result["error"]
        assert "Camera images retrieval failed" in result["message"]

    @pytest.mark.asyncio
    async def test_request_image_with_empty_devices(self, camera_repository, mock_client):
        """Test camera image request with empty devices list."""
        # Arrange
        installation_id = "12345"
        panel = "panel1"
        devices = []
        capabilities = "test_capabilities"
        
        mock_dto = Mock()
        mock_dto.success = True
        mock_dto.successful_requests = 0
        mock_dto.reference_id = "ref_empty"
        
        mock_client.request_image.return_value = mock_dto
        
        expected_result = CameraRequestImageResult(
            success=True,
            successful_requests=0,
            reference_id="ref_empty"
        )
        
        with patch('core.api.models.domain.camera_request_image.CameraRequestImageResult.from_dto') as mock_from_dto:
            mock_from_dto.return_value = expected_result
            
            # Act
            result = await camera_repository.request_image(
                installation_id, panel, devices, capabilities
            )
            
            # Assert
            assert result == expected_result
            mock_client.request_image.assert_called_once_with(
                installation_id=installation_id,
                panel=panel,
                devices=devices,
                capabilities=capabilities,
            )

    @pytest.mark.asyncio
    async def test_get_images_with_special_characters(self, camera_repository, mock_client):
        """Test get camera images with special characters in parameters."""
        # Arrange
        installation_id = "12345"
        panel = "panel-1"
        device = "device_1"
        zone_id = "zone-1"
        capabilities = "test_capabilities_with_special_chars"
        
        expected_images = {
            "success": True,
            "images": [],
            "count": 0
        }
        
        mock_client.get_images.return_value = expected_images
        
        # Act
        result = await camera_repository.get_images(
            installation_id, panel, device, zone_id, capabilities
        )
        
        # Assert
        assert result == expected_images
        mock_client.get_images.assert_called_once_with(
            installation_id=installation_id,
            panel=panel,
            device=device,
            zone_id=zone_id,
            capabilities=capabilities,
        )


if __name__ == "__main__":
    pytest.main([__file__])

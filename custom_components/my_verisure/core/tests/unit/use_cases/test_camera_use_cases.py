#!/usr/bin/env python3
"""
Unit tests for Camera Use Cases implementations.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from ....use_cases.implementations.refresh_camera_images_use_case_impl import (
    RefreshCameraImagesUseCaseImpl,
)
from ....use_cases.implementations.create_dummy_camera_images_use_case_impl import (
    CreateDummyCameraImagesUseCaseImpl,
)
from ....use_cases.interfaces.refresh_camera_images_use_case import (
    RefreshCameraImagesUseCase,
)
from ....use_cases.interfaces.create_dummy_camera_images_use_case import (
    CreateDummyCameraImagesUseCase,
)
from ....repositories.interfaces.camera_repository import CameraRepository
from ....repositories.interfaces.installation_repository import InstallationRepository
from ....api.models.domain.camera_request_image import CameraRequestImageResult
from ....api.exceptions import MyVerisureError


class TestRefreshCameraImagesUseCase:
    """Test cases for RefreshCameraImagesUseCase implementation."""

    @pytest.fixture
    def mock_camera_repository(self):
        """Create a mock camera repository."""
        mock_repo = Mock(spec=CameraRepository)
        mock_repo.request_image = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_installation_repository(self):
        """Create a mock installation repository."""
        mock_repo = Mock(spec=InstallationRepository)
        mock_repo.get_installation_services = AsyncMock()
        return mock_repo

    @pytest.fixture
    def refresh_use_case(self, mock_camera_repository, mock_installation_repository):
        """Create RefreshCameraImagesUseCase instance with mocked dependencies."""
        return RefreshCameraImagesUseCaseImpl(
            camera_repository=mock_camera_repository,
            installation_repository=mock_installation_repository
        )

    def test_refresh_use_case_implements_interface(self, refresh_use_case):
        """Test that RefreshCameraImagesUseCaseImpl implements RefreshCameraImagesUseCase interface."""
        assert isinstance(refresh_use_case, RefreshCameraImagesUseCase)

    @pytest.mark.asyncio
    async def test_refresh_camera_images_success(self, refresh_use_case, mock_camera_repository, mock_installation_repository):
        """Test successful camera images refresh."""
        # Arrange
        installation_id = "12345"
        
        # Mock installation services
        mock_services = Mock()
        mock_installation = Mock()
        mock_installation.panel = "PROTOCOL"
        mock_installation.capabilities = "default_capabilities"
        mock_services.installation = mock_installation
        mock_installation_repository.get_installation_services.return_value = mock_services
        
        # Mock camera repository response
        expected_result = CameraRequestImageResult(
            success=True,
            successful_requests=3,
            reference_id="ref_123"
        )
        mock_camera_repository.request_image.return_value = expected_result
        
        # Act
        result = await refresh_use_case.refresh_camera_images(installation_id)
        
        # Assert
        assert result == expected_result
        mock_installation_repository.get_installation_services.assert_called_once_with(installation_id)
        mock_camera_repository.request_image.assert_called_once_with(
            installation_id=installation_id,
            panel="PROTOCOL",
            devices=[],  # Empty devices list for refresh
            capabilities="default_capabilities"
        )

    @pytest.mark.asyncio
    async def test_refresh_camera_images_installation_error(self, refresh_use_case, mock_installation_repository):
        """Test camera images refresh when installation services fail."""
        # Arrange
        installation_id = "12345"
        mock_installation_repository.get_installation_services.side_effect = MyVerisureError("Installation not found")
        
        # Act
        result = await refresh_use_case.refresh_camera_images(installation_id)
        
        # Assert
        assert result.success is False
        assert result.successful_requests == 0
        assert result.reference_id is None

    @pytest.mark.asyncio
    async def test_refresh_camera_images_camera_error(self, refresh_use_case, mock_camera_repository, mock_installation_repository):
        """Test camera images refresh when camera request fails."""
        # Arrange
        installation_id = "12345"
        
        # Mock installation services
        mock_services = Mock()
        mock_installation = Mock()
        mock_installation.panel = "PROTOCOL"
        mock_installation.capabilities = "default_capabilities"
        mock_services.installation = mock_installation
        mock_installation_repository.get_installation_services.return_value = mock_services
        
        # Mock camera repository failure
        mock_camera_repository.request_image.return_value = CameraRequestImageResult(
            success=False,
            successful_requests=0,
            reference_id=None
        )
        
        # Act
        result = await refresh_use_case.refresh_camera_images(installation_id)
        
        # Assert
        assert result.success is False
        assert result.successful_requests == 0
        assert result.reference_id is None


class TestCreateDummyCameraImagesUseCase:
    """Test cases for CreateDummyCameraImagesUseCase implementation."""

    @pytest.fixture
    def mock_camera_repository(self):
        """Create a mock camera repository."""
        mock_repo = Mock(spec=CameraRepository)
        mock_repo.get_images = AsyncMock()
        return mock_repo

    @pytest.fixture
    def mock_installation_repository(self):
        """Create a mock installation repository."""
        mock_repo = Mock(spec=InstallationRepository)
        mock_repo.get_installation_services = AsyncMock()
        return mock_repo

    @pytest.fixture
    def create_dummy_use_case(self, mock_camera_repository, mock_installation_repository):
        """Create CreateDummyCameraImagesUseCase instance with mocked dependencies."""
        return CreateDummyCameraImagesUseCaseImpl(
            camera_repository=mock_camera_repository,
            installation_repository=mock_installation_repository
        )

    def test_create_dummy_use_case_implements_interface(self, create_dummy_use_case):
        """Test that CreateDummyCameraImagesUseCaseImpl implements CreateDummyCameraImagesUseCase interface."""
        assert isinstance(create_dummy_use_case, CreateDummyCameraImagesUseCase)

    @pytest.mark.asyncio
    async def test_create_dummy_camera_images_success(self, create_dummy_use_case, mock_camera_repository, mock_installation_repository):
        """Test successful dummy camera images creation."""
        # Arrange
        installation_id = "12345"
        device = "device1"
        zone_id = "zone1"
        
        # Mock installation services
        mock_services = Mock()
        mock_installation = Mock()
        mock_installation.panel = "PROTOCOL"
        mock_installation.capabilities = "default_capabilities"
        mock_services.installation = mock_installation
        mock_installation_repository.get_installation_services.return_value = mock_services
        
        # Mock camera repository response
        expected_images = {
            "success": True,
            "images": [
                {"id": "img1", "url": "http://example.com/img1.jpg"},
                {"id": "img2", "url": "http://example.com/img2.jpg"}
            ],
            "count": 2
        }
        mock_camera_repository.get_images.return_value = expected_images
        
        # Act
        result = await create_dummy_use_case.create_dummy_camera_images(
            installation_id, device, zone_id
        )
        
        # Assert
        assert result == expected_images
        mock_installation_repository.get_installation_services.assert_called_once_with(installation_id)
        mock_camera_repository.get_images.assert_called_once_with(
            installation_id=installation_id,
            panel="PROTOCOL",
            device=device,
            zone_id=zone_id,
            capabilities="default_capabilities"
        )

    @pytest.mark.asyncio
    async def test_create_dummy_camera_images_installation_error(self, create_dummy_use_case, mock_installation_repository):
        """Test dummy camera images creation when installation services fail."""
        # Arrange
        installation_id = "12345"
        device = "device1"
        zone_id = "zone1"
        mock_installation_repository.get_installation_services.side_effect = MyVerisureError("Installation not found")
        
        # Act
        result = await create_dummy_use_case.create_dummy_camera_images(
            installation_id, device, zone_id
        )
        
        # Assert
        assert result["success"] is False
        assert "error" in result
        assert "Installation not found" in result["error"]

    @pytest.mark.asyncio
    async def test_create_dummy_camera_images_camera_error(self, create_dummy_use_case, mock_camera_repository, mock_installation_repository):
        """Test dummy camera images creation when camera request fails."""
        # Arrange
        installation_id = "12345"
        device = "device1"
        zone_id = "zone1"
        
        # Mock installation services
        mock_services = Mock()
        mock_installation = Mock()
        mock_installation.panel = "PROTOCOL"
        mock_installation.capabilities = "default_capabilities"
        mock_services.installation = mock_installation
        mock_installation_repository.get_installation_services.return_value = mock_services
        
        # Mock camera repository failure
        mock_camera_repository.get_images.return_value = {
            "success": False,
            "error": "Camera error",
            "message": "Failed to get images"
        }
        
        # Act
        result = await create_dummy_use_case.create_dummy_camera_images(
            installation_id, device, zone_id
        )
        
        # Assert
        assert result["success"] is False
        assert result["error"] == "Camera error"
        assert result["message"] == "Failed to get images"

    @pytest.mark.asyncio
    async def test_create_dummy_camera_images_with_special_parameters(self, create_dummy_use_case, mock_camera_repository, mock_installation_repository):
        """Test dummy camera images creation with special parameters."""
        # Arrange
        installation_id = "12345"
        device = "device-1"
        zone_id = "zone_1"
        
        # Mock installation services
        mock_services = Mock()
        mock_installation = Mock()
        mock_installation.panel = "SDVFAST"
        mock_installation.capabilities = "advanced_capabilities"
        mock_services.installation = mock_installation
        mock_installation_repository.get_installation_services.return_value = mock_services
        
        # Mock camera repository response
        expected_images = {
            "success": True,
            "images": [],
            "count": 0
        }
        mock_camera_repository.get_images.return_value = expected_images
        
        # Act
        result = await create_dummy_use_case.create_dummy_camera_images(
            installation_id, device, zone_id
        )
        
        # Assert
        assert result == expected_images
        mock_camera_repository.get_images.assert_called_once_with(
            installation_id=installation_id,
            panel="SDVFAST",
            device=device,
            zone_id=zone_id,
            capabilities="advanced_capabilities"
        )


if __name__ == "__main__":
    pytest.main([__file__])

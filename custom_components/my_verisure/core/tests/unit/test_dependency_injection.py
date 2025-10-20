"""Unit tests for dependency injection system."""

from unittest.mock import patch, Mock
import pytest

from ...dependency_injection.container import (
    get_injector, setup_injector, get_dependency, clear_injector
)
from ...dependency_injection.providers import (
    setup_dependencies, get_auth_use_case, get_installation_use_case,
    get_alarm_use_case, get_get_installation_devices_use_case,
    get_refresh_camera_images_use_case, get_create_dummy_camera_images_use_case,
    get_auth_client, get_installation_client, get_alarm_client,
    get_camera_client, get_camera_repository, clear_dependencies
)


class TestDependencyInjectionContainer:
    """Test dependency injection container."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_injector()

    def teardown_method(self):
        """Clean up after each test."""
        clear_injector()

    def test_get_injector_not_setup(self):
        """Test getting injector when not set up."""
        with pytest.raises(RuntimeError, match="Injector not setup. Call setup_injector\\(\\) first."):
            get_injector()

    def test_setup_injector(self):
        """Test setting up injector."""
        mock_module = Mock()
        
        setup_injector(mock_module)
        
        injector = get_injector()
        assert injector is not None

    def test_get_dependency_success(self):
        """Test getting dependency successfully."""
        mock_module = Mock()
        mock_interface = Mock()
        mock_instance = Mock()
        
        # Mock the injector
        with patch('...dependency_injection.container.Injector') as mock_injector_class:
            mock_injector = Mock()
            mock_injector.get.return_value = mock_instance
            mock_injector_class.return_value = mock_injector
            
            setup_injector(mock_module)
            
            result = get_dependency(mock_interface)
            
            assert result == mock_instance
            mock_injector.get.assert_called_once_with(mock_interface)

    def test_get_dependency_failure(self):
        """Test getting dependency when injector not set up."""
        mock_interface = Mock()
        
        with pytest.raises(RuntimeError, match="Injector not setup. Call setup_injector\\(\\) first."):
            get_dependency(mock_interface)

    def test_clear_injector(self):
        """Test clearing injector."""
        mock_module = Mock()
        
        setup_injector(mock_module)
        assert get_injector() is not None
        
        clear_injector()
        
        with pytest.raises(RuntimeError, match="Injector not setup. Call setup_injector\\(\\) first."):
            get_injector()


class TestDependencyInjectionProviders:
    """Test dependency injection providers."""

    def setup_method(self):
        """Set up test fixtures."""
        clear_dependencies()

    def teardown_method(self):
        """Clean up after each test."""
        clear_dependencies()

    def test_setup_dependencies(self):
        """Test setting up dependencies."""
        with patch('...dependency_injection.providers.MyVerisureModule') as mock_module_class:
            mock_module = Mock()
            mock_module_class.return_value = mock_module
            
            with patch('...dependency_injection.providers.setup_injector') as mock_setup:
                setup_dependencies()
                
                mock_module_class.assert_called_once()
                mock_setup.assert_called_once_with(mock_module)

    def test_get_auth_use_case(self):
        """Test getting auth use case."""
        mock_auth_use_case = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_auth_use_case):
            result = get_auth_use_case()
            
            assert result == mock_auth_use_case

    def test_get_installation_use_case(self):
        """Test getting installation use case."""
        mock_installation_use_case = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_installation_use_case):
            result = get_installation_use_case()
            
            assert result == mock_installation_use_case

    def test_get_alarm_use_case(self):
        """Test getting alarm use case."""
        mock_alarm_use_case = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_alarm_use_case):
            result = get_alarm_use_case()
            
            assert result == mock_alarm_use_case

    def test_get_get_installation_devices_use_case(self):
        """Test getting get installation devices use case."""
        mock_use_case = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_use_case):
            result = get_get_installation_devices_use_case()
            
            assert result == mock_use_case

    def test_get_refresh_camera_images_use_case(self):
        """Test getting refresh camera images use case."""
        mock_use_case = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_use_case):
            result = get_refresh_camera_images_use_case()
            
            assert result == mock_use_case

    def test_get_create_dummy_camera_images_use_case(self):
        """Test getting create dummy camera images use case."""
        mock_use_case = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_use_case):
            result = get_create_dummy_camera_images_use_case()
            
            assert result == mock_use_case

    def test_get_auth_client(self):
        """Test getting auth client."""
        mock_auth_client = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_auth_client):
            result = get_auth_client()
            
            assert result == mock_auth_client

    def test_get_installation_client(self):
        """Test getting installation client."""
        mock_installation_client = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_installation_client):
            result = get_installation_client()
            
            assert result == mock_installation_client

    def test_get_alarm_client(self):
        """Test getting alarm client."""
        mock_alarm_client = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_alarm_client):
            result = get_alarm_client()
            
            assert result == mock_alarm_client

    def test_get_camera_client(self):
        """Test getting camera client."""
        mock_camera_client = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_camera_client):
            result = get_camera_client()
            
            assert result == mock_camera_client

    def test_get_camera_repository(self):
        """Test getting camera repository."""
        mock_camera_repository = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_camera_repository):
            result = get_camera_repository()
            
            assert result == mock_camera_repository

    def test_clear_dependencies(self):
        """Test clearing dependencies."""
        with patch('...dependency_injection.providers.clear_injector') as mock_clear:
            clear_dependencies()
            
            mock_clear.assert_called_once()

    def test_provider_functions_with_injector_error(self):
        """Test provider functions when injector is not set up."""
        with patch('...dependency_injection.providers.get_dependency', side_effect=RuntimeError("Injector not setup")):
            with pytest.raises(RuntimeError, match="Injector not setup"):
                get_auth_use_case()

    def test_setup_dependencies_with_module_error(self):
        """Test setup dependencies when module creation fails."""
        with patch('...dependency_injection.providers.MyVerisureModule', side_effect=Exception("Module error")):
            with pytest.raises(Exception, match="Module error"):
                setup_dependencies()

    def test_provider_functions_with_dependency_error(self):
        """Test provider functions when dependency resolution fails."""
        with patch('...dependency_injection.providers.get_dependency', side_effect=Exception("Dependency error")):
            with pytest.raises(Exception, match="Dependency error"):
                get_auth_use_case()

    def test_all_provider_functions(self):
        """Test all provider functions work correctly."""
        mock_dependency = Mock()
        
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_dependency):
            # Test all provider functions
            assert get_auth_use_case() == mock_dependency
            assert get_installation_use_case() == mock_dependency
            assert get_alarm_use_case() == mock_dependency
            assert get_get_installation_devices_use_case() == mock_dependency
            assert get_refresh_camera_images_use_case() == mock_dependency
            assert get_create_dummy_camera_images_use_case() == mock_dependency
            assert get_auth_client() == mock_dependency
            assert get_installation_client() == mock_dependency
            assert get_alarm_client() == mock_dependency
            assert get_camera_client() == mock_dependency
            assert get_camera_repository() == mock_dependency

    def test_dependency_injection_lifecycle(self):
        """Test complete dependency injection lifecycle."""
        # Setup
        with patch('...dependency_injection.providers.MyVerisureModule') as mock_module_class:
            mock_module = Mock()
            mock_module_class.return_value = mock_module
            
            with patch('...dependency_injection.providers.setup_injector') as mock_setup:
                setup_dependencies()
                
                mock_setup.assert_called_once_with(mock_module)
        
        # Get dependencies
        mock_dependency = Mock()
        with patch('...dependency_injection.providers.get_dependency', return_value=mock_dependency):
            result = get_auth_use_case()
            assert result == mock_dependency
        
        # Clear dependencies
        with patch('...dependency_injection.providers.clear_injector') as mock_clear:
            clear_dependencies()
            mock_clear.assert_called_once()

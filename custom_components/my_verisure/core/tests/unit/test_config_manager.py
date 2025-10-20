"""Unit tests for ConfigManager."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest

from ...config_manager import ConfigManager, get_config_manager, reset_config_manager


class TestConfigManager:
    """Test ConfigManager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset global instance before each test
        reset_config_manager()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()
        
        # Mock file manager
        self.mock_file_manager = Mock()
        self.mock_file_manager.load_json.return_value = None
        self.mock_file_manager.save_json.return_value = True
        self.mock_file_manager.get_file_path.return_value = Path(self.temp_dir) / "config.json"
        self.mock_file_manager.get_file_size.return_value = 1024

    def teardown_method(self):
        """Clean up after each test."""
        reset_config_manager()

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            config_manager = ConfigManager()
            
            assert config_manager._file_manager == self.mock_file_manager
            assert config_manager._config_file == "my_verisure_config.json"
            assert "version" in config_manager._default_config
            assert "debug" in config_manager._default_config

    def test_get_config_default(self):
        """Test getting default configuration."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            config_manager = ConfigManager()
            result = config_manager.get_config()
            
            assert result["version"] == "1.0.0"
            assert result["debug"] is False
            assert result["timeout"] == 30
            assert result["retry_attempts"] == 3
            assert result["cache_duration"] == 300
            assert "features" in result
            assert "notifications" in result

    def test_get_config_from_file(self):
        """Test getting configuration from file."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock file content
            file_config = {
                "version": "1.0.0",
                "debug": True,
                "timeout": 60,
                "features": {
                    "alarm": True,
                    "sensors": False,
                    "cameras": True
                }
            }
            self.mock_file_manager.load_json.return_value = file_config
            
            config_manager = ConfigManager()
            result = config_manager.get_config()
            
            # Should merge with defaults
            assert result["debug"] is True
            assert result["timeout"] == 60
            assert result["retry_attempts"] == 3  # From defaults
            assert result["features"]["alarm"] is True
            assert result["features"]["sensors"] is False
            assert result["features"]["cameras"] is True

    def test_get_config_file_error(self):
        """Test getting configuration when file loading fails."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock file loading error
            self.mock_file_manager.load_json.side_effect = Exception("File error")
            
            config_manager = ConfigManager()
            result = config_manager.get_config()
            
            # Should return defaults
            assert result["version"] == "1.0.0"
            assert result["debug"] is False

    def test_save_config_success(self):
        """Test successful configuration saving."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            config_manager = ConfigManager()
            test_config = {"debug": True, "timeout": 60}
            
            result = config_manager.save_config(test_config)
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the call arguments
            call_args = self.mock_file_manager.save_json.call_args
            assert call_args[0][0] == "my_verisure_config.json"
            saved_data = call_args[0][1]
            assert "metadata" in saved_data
            assert "config" in saved_data
            assert saved_data["config"] == test_config

    def test_save_config_failure(self):
        """Test configuration saving failure."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock save failure
            self.mock_file_manager.save_json.return_value = False
            
            config_manager = ConfigManager()
            test_config = {"debug": True}
            
            result = config_manager.save_config(test_config)
            
            assert result is False

    def test_update_config_success(self):
        """Test successful configuration update."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock existing config
            existing_config = {"debug": False, "timeout": 30}
            self.mock_file_manager.load_json.return_value = existing_config
            
            config_manager = ConfigManager()
            updates = {"debug": True, "timeout": 60}
            
            result = config_manager.update_config(updates)
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the updated config
            call_args = self.mock_file_manager.save_json.call_args
            saved_data = call_args[0][1]["config"]
            assert saved_data["debug"] is True
            assert saved_data["timeout"] == 60

    def test_get_setting(self):
        """Test getting a specific setting."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock existing config
            existing_config = {"debug": True, "timeout": 60}
            self.mock_file_manager.load_json.return_value = existing_config
            
            config_manager = ConfigManager()
            
            # Test existing setting
            result = config_manager.get_setting("debug")
            assert result is True
            
            # Test non-existing setting with default
            result = config_manager.get_setting("nonexistent", "default_value")
            assert result == "default_value"
            
            # Test non-existing setting without default
            result = config_manager.get_setting("nonexistent")
            assert result is None

    def test_set_setting(self):
        """Test setting a specific setting."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock existing config
            existing_config = {"debug": False}
            self.mock_file_manager.load_json.return_value = existing_config
            
            config_manager = ConfigManager()
            
            result = config_manager.set_setting("debug", True)
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            config_manager = ConfigManager()
            
            result = config_manager.reset_to_defaults()
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify defaults were saved
            call_args = self.mock_file_manager.save_json.call_args
            saved_data = call_args[0][1]["config"]
            assert saved_data["version"] == "1.0.0"
            assert saved_data["debug"] is False

    def test_export_config_success(self):
        """Test successful configuration export."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock existing config
            existing_config = {"debug": True, "timeout": 60}
            self.mock_file_manager.load_json.return_value = existing_config
            
            config_manager = ConfigManager()
            
            result = config_manager.export_config("exported_config.json")
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_with("exported_config.json", existing_config)

    def test_export_config_failure(self):
        """Test configuration export failure."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock save failure
            self.mock_file_manager.save_json.return_value = False
            
            config_manager = ConfigManager()
            
            result = config_manager.export_config("exported_config.json")
            
            assert result is False

    def test_import_config_success(self):
        """Test successful configuration import."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock import file content
            import_config = {"debug": True, "timeout": 60}
            self.mock_file_manager.load_json.return_value = import_config
            
            config_manager = ConfigManager()
            
            result = config_manager.import_config("imported_config.json")
            
            assert result is True
            self.mock_file_manager.load_json.assert_called_with("imported_config.json")
            self.mock_file_manager.save_json.assert_called_once()

    def test_import_config_file_not_found(self):
        """Test configuration import when file doesn't exist."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock file not found
            self.mock_file_manager.load_json.return_value = None
            
            config_manager = ConfigManager()
            
            result = config_manager.import_config("nonexistent.json")
            
            assert result is False

    def test_get_timestamp(self):
        """Test timestamp generation."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            config_manager = ConfigManager()
            
            timestamp = config_manager._get_timestamp()
            
            # Should be a valid ISO format timestamp
            assert isinstance(timestamp, str)
            assert "T" in timestamp
            assert len(timestamp) > 10

    def test_get_config_info_exists(self):
        """Test getting configuration info when file exists."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock existing config with metadata
            config_data = {
                "metadata": {
                    "saved_at": "2024-01-01T00:00:00",
                    "version": "1.0.0"
                },
                "config": {"debug": True}
            }
            self.mock_file_manager.load_json.return_value = config_data
            
            config_manager = ConfigManager()
            result = config_manager.get_config_info()
            
            assert result["exists"] is True
            assert result["using_defaults"] is False
            assert result["saved_at"] == "2024-01-01T00:00:00"
            assert result["version"] == "1.0.0"
            assert result["file_size"] == 1024

    def test_get_config_info_not_exists(self):
        """Test getting configuration info when file doesn't exist."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock no config file
            self.mock_file_manager.load_json.return_value = None
            
            config_manager = ConfigManager()
            result = config_manager.get_config_info()
            
            assert result["exists"] is False
            assert result["using_defaults"] is True
            assert "file_path" in result

    def test_get_config_info_error(self):
        """Test getting configuration info when error occurs."""
        with patch('...config_manager.get_file_manager', return_value=self.mock_file_manager):
            # Mock error
            self.mock_file_manager.load_json.side_effect = Exception("File error")
            
            config_manager = ConfigManager()
            result = config_manager.get_config_info()
            
            assert "error" in result
            assert "File error" in result["error"]


class TestConfigManagerGlobal:
    """Test ConfigManager global functions."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config_manager()

    def teardown_method(self):
        """Clean up after each test."""
        reset_config_manager()

    def test_get_config_manager_singleton(self):
        """Test ConfigManager singleton behavior."""
        # First call should create instance
        manager1 = get_config_manager()
        assert isinstance(manager1, ConfigManager)
        
        # Second call should return same instance
        manager2 = get_config_manager()
        assert manager1 is manager2

    def test_reset_config_manager(self):
        """Test resetting ConfigManager."""
        # Get instance
        manager1 = get_config_manager()
        
        # Reset
        reset_config_manager()
        
        # Get new instance
        manager2 = get_config_manager()
        assert manager1 is not manager2

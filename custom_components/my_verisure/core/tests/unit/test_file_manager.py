"""Unit tests for FileManager."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open
import pytest

from ...file_manager import FileManager, get_file_manager, reset_file_manager


class TestFileManager:
    """Test FileManager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset global instance before each test
        reset_file_manager()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def teardown_method(self):
        """Clean up after each test."""
        # Reset global instance
        reset_file_manager()
        
        # Restore original working directory
        os.chdir(self.original_cwd)
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_manager_initialization(self):
        """Test FileManager initialization."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            assert file_manager._project_root == Path(self.temp_dir)
            assert file_manager._data_dir == Path(self.temp_dir) / "data"
            mock_detect.assert_called_once()

    def test_detect_project_root_home_assistant_env(self):
        """Test project root detection in Home Assistant environment."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/config/custom_components/my_verisure")
            
            file_manager = FileManager()
            result = file_manager._detect_project_root()
            
            assert result == Path("/config/custom_components/my_verisure")

    def test_detect_project_root_cli_project(self):
        """Test project root detection in CLI project."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path(self.temp_dir)
            
            # Create custom_components/my_verisure structure
            custom_components_dir = Path(self.temp_dir) / "custom_components" / "my_verisure"
            custom_components_dir.mkdir(parents=True)
            
            file_manager = FileManager()
            result = file_manager._detect_project_root()
            
            assert result == custom_components_dir

    def test_detect_project_root_fallback(self):
        """Test project root detection fallback."""
        with patch('pathlib.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager._detect_project_root()
            
            # Should fallback to current directory
            assert result == Path(self.temp_dir)

    def test_get_project_root(self):
        """Test getting project root."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.get_project_root()
            
            assert result == Path(self.temp_dir)

    def test_get_data_directory(self):
        """Test getting data directory."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.get_data_directory()
            
            assert result == Path(self.temp_dir) / "data"

    def test_save_text_success(self):
        """Test successful text saving."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.save_text("test.txt", "Hello World")
            
            assert result is True
            assert (Path(self.temp_dir) / "data" / "test.txt").exists()
            
            # Verify content
            with open(Path(self.temp_dir) / "data" / "test.txt", 'r') as f:
                content = f.read()
            assert content == "Hello World"

    def test_save_text_failure(self):
        """Test text saving failure."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Mock open to raise an exception
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = file_manager.save_text("test.txt", "Hello World")
                
                assert result is False

    def test_load_text_success(self):
        """Test successful text loading."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file
            test_file = Path(self.temp_dir) / "data" / "test.txt"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("Hello World")
            
            result = file_manager.load_text("test.txt")
            
            assert result == "Hello World"

    def test_load_text_file_not_found(self):
        """Test text loading when file doesn't exist."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.load_text("nonexistent.txt")
            
            assert result is None

    def test_load_text_failure(self):
        """Test text loading failure."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file
            test_file = Path(self.temp_dir) / "data" / "test.txt"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("Hello World")
            
            # Mock open to raise an exception
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = file_manager.load_text("test.txt")
                
                assert result is None

    def test_save_json_success(self):
        """Test successful JSON saving."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            test_data = {"key": "value", "number": 123}
            result = file_manager.save_json("test.json", test_data)
            
            assert result is True
            assert (Path(self.temp_dir) / "data" / "test.json").exists()
            
            # Verify content
            with open(Path(self.temp_dir) / "data" / "test.json", 'r') as f:
                content = json.load(f)
            assert content == test_data

    def test_save_json_failure(self):
        """Test JSON saving failure."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Mock open to raise an exception
            with patch('builtins.open', side_effect=IOError("Permission denied")):
                result = file_manager.save_json("test.json", {"key": "value"})
                
                assert result is False

    def test_load_json_success(self):
        """Test successful JSON loading."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file
            test_file = Path(self.temp_dir) / "data" / "test.json"
            test_file.parent.mkdir(parents=True)
            test_data = {"key": "value", "number": 123}
            test_file.write_text(json.dumps(test_data))
            
            result = file_manager.load_json("test.json")
            
            assert result == test_data

    def test_load_json_file_not_found(self):
        """Test JSON loading when file doesn't exist."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.load_json("nonexistent.json")
            
            assert result is None

    def test_load_json_invalid_json(self):
        """Test JSON loading with invalid JSON."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file with invalid JSON
            test_file = Path(self.temp_dir) / "data" / "test.json"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("invalid json content")
            
            result = file_manager.load_json("test.json")
            
            assert result is None

    def test_file_exists(self):
        """Test file existence check."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Test with existing file
            test_file = Path(self.temp_dir) / "data" / "test.txt"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("Hello World")
            
            assert file_manager.file_exists("test.txt") is True
            assert file_manager.file_exists("nonexistent.txt") is False

    def test_delete_file_success(self):
        """Test successful file deletion."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file
            test_file = Path(self.temp_dir) / "data" / "test.txt"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("Hello World")
            
            result = file_manager.delete_file("test.txt")
            
            assert result is True
            assert not test_file.exists()

    def test_delete_file_not_found(self):
        """Test file deletion when file doesn't exist."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.delete_file("nonexistent.txt")
            
            assert result is False

    def test_delete_files_by_prefix(self):
        """Test deleting files by prefix."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test files
            data_dir = Path(self.temp_dir) / "data"
            data_dir.mkdir(parents=True)
            
            (data_dir / "test1.txt").write_text("content1")
            (data_dir / "test2.txt").write_text("content2")
            (data_dir / "other.txt").write_text("content3")
            
            result = file_manager.delete_files_by_prefix("test")
            
            assert result == 2
            assert not (data_dir / "test1.txt").exists()
            assert not (data_dir / "test2.txt").exists()
            assert (data_dir / "other.txt").exists()

    def test_save_binary_success(self):
        """Test successful binary saving."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            test_data = b"binary content"
            result = file_manager.save_binary("test.bin", test_data)
            
            assert result is True
            assert (Path(self.temp_dir) / "data" / "test.bin").exists()
            
            # Verify content
            with open(Path(self.temp_dir) / "data" / "test.bin", 'rb') as f:
                content = f.read()
            assert content == test_data

    def test_save_base64_image_success(self):
        """Test successful base64 image saving."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create base64 encoded data
            import base64
            test_data = b"image data"
            base64_data = base64.b64encode(test_data).decode('utf-8')
            
            result = file_manager.save_base64_image("test.jpg", base64_data)
            
            assert result is True
            assert (Path(self.temp_dir) / "data" / "test.jpg").exists()
            
            # Verify content
            with open(Path(self.temp_dir) / "data" / "test.jpg", 'rb') as f:
                content = f.read()
            assert content == test_data

    def test_list_files(self):
        """Test listing files."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test files
            data_dir = Path(self.temp_dir) / "data"
            data_dir.mkdir(parents=True)
            
            (data_dir / "test1.txt").write_text("content1")
            (data_dir / "test2.txt").write_text("content2")
            (data_dir / "other.json").write_text("{}")
            
            # Test listing all files
            files = file_manager.list_files()
            assert len(files) == 3
            assert "test1.txt" in files
            assert "test2.txt" in files
            assert "other.json" in files
            
            # Test listing with pattern
            txt_files = file_manager.list_files("*.txt")
            assert len(txt_files) == 2
            assert "test1.txt" in txt_files
            assert "test2.txt" in txt_files

    def test_get_file_path(self):
        """Test getting file path."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            result = file_manager.get_file_path("test.txt")
            
            assert result == Path(self.temp_dir) / "data" / "test.txt"

    def test_get_file_size(self):
        """Test getting file size."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file
            test_file = Path(self.temp_dir) / "data" / "test.txt"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("Hello World")
            
            result = file_manager.get_file_size("test.txt")
            
            assert result == len("Hello World")
            
            # Test with non-existent file
            result = file_manager.get_file_size("nonexistent.txt")
            assert result is None

    def test_save_device_identifiers(self):
        """Test saving device identifiers."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            test_data = {"idDevice": "device_123", "uuid": "uuid_456"}
            result = file_manager.save_device_identifiers(test_data)
            
            assert result is True
            assert (Path.cwd() / "device_identifiers.json").exists()
            
            # Verify content
            with open(Path.cwd() / "device_identifiers.json", 'r') as f:
                content = json.load(f)
            assert content == test_data

    def test_load_device_identifiers(self):
        """Test loading device identifiers."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Create test file
            test_data = {"idDevice": "device_123", "uuid": "uuid_456"}
            test_file = Path.cwd() / "device_identifiers.json"
            test_file.write_text(json.dumps(test_data))
            
            result = file_manager.load_device_identifiers()
            
            assert result == test_data

    def test_device_identifiers_exists(self):
        """Test device identifiers existence check."""
        with patch.object(FileManager, '_detect_project_root') as mock_detect:
            mock_detect.return_value = Path(self.temp_dir)
            
            file_manager = FileManager()
            
            # Test with non-existent file
            assert file_manager.device_identifiers_exists() is False
            
            # Create test file
            test_file = Path.cwd() / "device_identifiers.json"
            test_file.write_text("{}")
            
            assert file_manager.device_identifiers_exists() is True


class TestFileManagerGlobal:
    """Test FileManager global functions."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_file_manager()

    def teardown_method(self):
        """Clean up after each test."""
        reset_file_manager()

    def test_get_file_manager_singleton(self):
        """Test FileManager singleton behavior."""
        # First call should create instance
        manager1 = get_file_manager()
        assert isinstance(manager1, FileManager)
        
        # Second call should return same instance
        manager2 = get_file_manager()
        assert manager1 is manager2

    def test_reset_file_manager(self):
        """Test resetting FileManager."""
        # Get instance
        manager1 = get_file_manager()
        
        # Reset
        reset_file_manager()
        
        # Get new instance
        manager2 = get_file_manager()
        assert manager1 is not manager2

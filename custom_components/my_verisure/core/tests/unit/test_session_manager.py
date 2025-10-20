"""Unit tests for SessionManager."""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, Mock, mock_open
import pytest

from ...session_manager import SessionManager, _session_manager_instance


class TestSessionManager:
    """Test SessionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset global instance
        global _session_manager_instance
        _session_manager_instance = None
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.original_home = os.path.expanduser("~")
        
        # Mock home directory
        self.mock_home = os.path.join(self.temp_dir, "home")
        os.makedirs(self.mock_home, exist_ok=True)

    def teardown_method(self):
        """Clean up after each test."""
        # Reset global instance
        global _session_manager_instance
        _session_manager_instance = None
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_session_manager_initialization(self):
        """Test SessionManager initialization."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                
                assert session_manager._is_authenticated is False
                assert session_manager.current_installation is None
                assert session_manager.username is None
                assert session_manager.password is None
                assert session_manager.hash_token is None
                assert session_manager.refresh_token is None
                assert session_manager.session_timestamp is None

    def test_get_session_file_path(self):
        """Test getting session file path."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                file_path = session_manager._get_session_file_path()
                
                expected_path = os.path.join(self.mock_home, ".my_verisure", "session.json")
                assert file_path == expected_path
                
                # Verify directory was created
                assert os.path.exists(os.path.dirname(file_path))

    def test_is_authenticated_no_credentials(self):
        """Test authentication check with no credentials."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                
                assert session_manager.is_authenticated is False

    def test_is_authenticated_no_username(self):
        """Test authentication check with no username."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.password = "password"
                session_manager.hash_token = "token"
                
                assert session_manager.is_authenticated is False

    def test_is_authenticated_no_password(self):
        """Test authentication check with no password."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.username = "user"
                session_manager.hash_token = "token"
                
                assert session_manager.is_authenticated is False

    def test_is_authenticated_no_token(self):
        """Test authentication check with no token."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.username = "user"
                session_manager.password = "password"
                
                assert session_manager.is_authenticated is False

    def test_is_authenticated_valid_credentials(self):
        """Test authentication check with valid credentials."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                with patch.object(SessionManager, '_is_token_valid', return_value=True):
                    session_manager = SessionManager()
                    session_manager.username = "user"
                    session_manager.password = "password"
                    session_manager.hash_token = "token"
                    
                    assert session_manager.is_authenticated is True

    def test_is_authenticated_invalid_token(self):
        """Test authentication check with invalid token."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                with patch.object(SessionManager, '_is_token_valid', return_value=False):
                    session_manager = SessionManager()
                    session_manager.username = "user"
                    session_manager.password = "password"
                    session_manager.hash_token = "token"
                    
                    assert session_manager.is_authenticated is False

    def test_load_session_success(self):
        """Test successful session loading."""
        session_data = {
            "username": "test_user",
            "password": "test_password",
            "hash_token": "test_hash",
            "refresh_token": "test_refresh",
            "session_timestamp": 1640995200,
            "current_installation": "inst123"
        }
        
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch('builtins.open', mock_open(read_data=json.dumps(session_data))):
                with patch('os.path.exists', return_value=True):
                    session_manager = SessionManager()
                    
                    assert session_manager.username == "test_user"
                    assert session_manager.password == "test_password"
                    assert session_manager.hash_token == "test_hash"
                    assert session_manager.refresh_token == "test_refresh"
                    assert session_manager.session_timestamp == 1640995200
                    assert session_manager.current_installation == "inst123"

    def test_load_session_file_not_found(self):
        """Test session loading when file doesn't exist."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch('os.path.exists', return_value=False):
                session_manager = SessionManager()
                
                assert session_manager.username is None
                assert session_manager.password is None
                assert session_manager.hash_token is None
                assert session_manager.refresh_token is None
                assert session_manager.session_timestamp is None
                assert session_manager.current_installation is None

    def test_load_session_invalid_json(self):
        """Test session loading with invalid JSON."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch('builtins.open', mock_open(read_data="invalid json")):
                with patch('os.path.exists', return_value=True):
                    session_manager = SessionManager()
                    
                    # Should not crash and should have default values
                    assert session_manager.username is None
                    assert session_manager.password is None

    def test_load_session_file_error(self):
        """Test session loading with file error."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch('os.path.exists', return_value=True):
                with patch('builtins.open', side_effect=IOError("Permission denied")):
                    session_manager = SessionManager()
                    
                    # Should not crash and should have default values
                    assert session_manager.username is None
                    assert session_manager.password is None

    def test_save_session_success(self):
        """Test successful session saving."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.username = "test_user"
                session_manager.password = "test_password"
                session_manager.hash_token = "test_hash"
                session_manager.refresh_token = "test_refresh"
                session_manager.session_timestamp = 1640995200
                session_manager.current_installation = "inst123"
                
                with patch('builtins.open', mock_open()) as mock_file:
                    result = session_manager.save_session()
                    
                    assert result is True
                    mock_file.assert_called_once()
                    
                    # Verify the saved data
                    call_args = mock_file.call_args
                    assert 'w' in call_args[0][1]  # File opened in write mode

    def test_save_session_failure(self):
        """Test session saving failure."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.username = "test_user"
                
                with patch('builtins.open', side_effect=IOError("Permission denied")):
                    result = session_manager.save_session()
                    
                    assert result is False

    def test_clear_session(self):
        """Test clearing session."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.username = "test_user"
                session_manager.password = "test_password"
                session_manager.hash_token = "test_hash"
                session_manager.refresh_token = "test_refresh"
                session_manager.session_timestamp = 1640995200
                session_manager.current_installation = "inst123"
                
                session_manager.clear_session()
                
                assert session_manager.username is None
                assert session_manager.password is None
                assert session_manager.hash_token is None
                assert session_manager.refresh_token is None
                assert session_manager.session_timestamp is None
                assert session_manager.current_installation is None

    def test_set_credentials(self):
        """Test setting credentials."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                
                session_manager.set_credentials("test_user", "test_password")
                
                assert session_manager.username == "test_user"
                assert session_manager.password == "test_password"

    def test_set_tokens(self):
        """Test setting tokens."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                
                session_manager.set_tokens("test_hash", "test_refresh")
                
                assert session_manager.hash_token == "test_hash"
                assert session_manager.refresh_token == "test_refresh"

    def test_set_current_installation(self):
        """Test setting current installation."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                
                session_manager.set_current_installation("inst123")
                
                assert session_manager.current_installation == "inst123"

    def test_get_session_info(self):
        """Test getting session information."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.username = "test_user"
                session_manager.hash_token = "test_hash"
                session_manager.current_installation = "inst123"
                session_manager.session_timestamp = 1640995200
                
                info = session_manager.get_session_info()
                
                assert info["username"] == "test_user"
                assert info["has_token"] is True
                assert info["current_installation"] == "inst123"
                assert info["session_timestamp"] == 1640995200
                assert "session_age_seconds" in info

    def test_is_token_valid_with_valid_token(self):
        """Test token validation with valid token."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                with patch('...session_manager.is_jwt_expired', return_value=False):
                    session_manager = SessionManager()
                    session_manager.hash_token = "valid_token"
                    
                    result = session_manager._is_token_valid()
                    assert result is True

    def test_is_token_valid_with_expired_token(self):
        """Test token validation with expired token."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                with patch('...session_manager.is_jwt_expired', return_value=True):
                    session_manager = SessionManager()
                    session_manager.hash_token = "expired_token"
                    
                    result = session_manager._is_token_valid()
                    assert result is False

    def test_is_token_valid_no_token(self):
        """Test token validation with no token."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                session_manager = SessionManager()
                session_manager.hash_token = None
                
                result = session_manager._is_token_valid()
                assert result is False

    def test_session_manager_singleton(self):
        """Test SessionManager singleton behavior."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                # First call should create instance
                session_manager1 = SessionManager()
                assert isinstance(session_manager1, SessionManager)
                
                # Second call should return same instance
                session_manager2 = SessionManager()
                assert session_manager1 is session_manager2

    def test_session_manager_with_mocked_time(self):
        """Test SessionManager with mocked time."""
        with patch('os.path.expanduser', return_value=self.mock_home):
            with patch.object(SessionManager, '_load_session'):
                with patch('time.time', return_value=1640995200):
                    session_manager = SessionManager()
                    session_manager.session_timestamp = 1640995200
                    
                    info = session_manager.get_session_info()
                    assert info["session_age_seconds"] == 0

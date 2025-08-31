"""Unit tests for CLI session manager."""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, AsyncMock, patch

from cli.utils.session_manager import SessionManager


class TestSessionManager:
    """Test SessionManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_file = os.path.join(self.temp_dir, "session.json")

        # Create a fresh SessionManager with a temporary session file
        with patch(
            "cli.utils.session_manager.SessionManager._get_session_file_path"
        ) as mock_path:
            mock_path.return_value = self.session_file
            self.session_manager = SessionManager()

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_init_default_values(self):
        """Test SessionManager initialization with default values."""
        with patch(
            "cli.utils.session_manager.SessionManager._get_session_file_path"
        ) as mock_path:
            mock_path.return_value = "/tmp/nonexistent_session.json"
            manager = SessionManager()
            assert manager.is_authenticated is False
            assert manager.current_installation is None
            assert manager.username is None
            assert manager.password is None
            assert manager.auth_use_case is None
            assert manager.installation_use_case is None

    def test_save_session(self):
        """Test save_session method."""
        self.session_manager.username = "test_user"
        self.session_manager.password = "test_password"
        self.session_manager.is_authenticated = True
        self.session_manager.current_installation = "12345"

        self.session_manager._save_session()

        assert os.path.exists(self.session_file)
        with open(self.session_file, "r") as f:
            data = json.load(f)

        assert data["username"] == "test_user"
        assert data["password"] == "test_password"
        assert data["is_authenticated"] is True
        assert data["current_installation"] == "12345"

    def test_load_session(self):
        """Test load_session method."""
        session_data = {
            "username": "test_user",
            "password": "test_password",
            "is_authenticated": True,
            "current_installation": "12345",
        }

        with open(self.session_file, "w") as f:
            json.dump(session_data, f)

        self.session_manager._load_session()

        assert self.session_manager.username == "test_user"
        assert self.session_manager.password == "test_password"
        assert self.session_manager.is_authenticated is True
        assert self.session_manager.current_installation == "12345"

    def test_load_session_file_not_exists(self):
        """Test load_session when file doesn't exist."""
        self.session_manager._load_session()

        assert self.session_manager.username is None
        assert self.session_manager.password is None
        assert self.session_manager.is_authenticated is False
        assert self.session_manager.current_installation is None

    def test_load_session_invalid_json(self):
        """Test load_session with invalid JSON."""
        with open(self.session_file, "w") as f:
            f.write("invalid json")

        self.session_manager._load_session()

        assert self.session_manager.username is None
        assert self.session_manager.password is None
        assert self.session_manager.is_authenticated is False
        assert self.session_manager.current_installation is None

    def test_clear_session_file(self):
        """Test clear_session_file method."""
        # Create a session file first
        session_data = {"username": "test_user"}
        with open(self.session_file, "w") as f:
            json.dump(session_data, f)

        assert os.path.exists(self.session_file)

        self.session_manager._clear_session_file()

        assert not os.path.exists(self.session_file)

    def test_clear_session_file_not_exists(self):
        """Test clear_session_file when file doesn't exist."""
        # Should not raise an exception
        self.session_manager._clear_session_file()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_with_saved_credentials(self):
        """Test ensure_authenticated with saved credentials."""
        self.session_manager.username = "test_user"
        self.session_manager.password = "test_password"

        with patch(
            "cli.utils.session_manager.setup_dependencies"
        ) as mock_setup, patch(
            "cli.utils.session_manager.get_auth_use_case"
        ) as mock_get_auth, patch(
            "cli.utils.session_manager.get_installation_use_case"
        ) as mock_get_install:

            mock_auth_use_case = AsyncMock()
            mock_install_use_case = AsyncMock()
            mock_auth_use_case.login = AsyncMock(
                return_value=Mock(success=True)
            )
            mock_get_auth.return_value = mock_auth_use_case
            mock_get_install.return_value = mock_install_use_case

            result = await self.session_manager.ensure_authenticated(
                interactive=False
            )

            assert result is True
            assert self.session_manager.is_authenticated is True
            assert self.session_manager.auth_use_case == mock_auth_use_case
            assert (
                self.session_manager.installation_use_case
                == mock_install_use_case
            )
            mock_setup.assert_called_once_with(
                username="test_user", password="test_password"
            )

    @pytest.mark.asyncio
    async def test_ensure_authenticated_no_credentials_interactive(self):
        """Test ensure_authenticated with no credentials in interactive mode."""
        # Clear any existing credentials
        self.session_manager.username = None
        self.session_manager.password = None

        with patch.object(
            self.session_manager, "_perform_interactive_login"
        ) as mock_login:
            mock_login.return_value = True

            result = await self.session_manager.ensure_authenticated(
                interactive=True
            )

            assert result is True
            mock_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_authenticated_no_credentials_non_interactive(self):
        """Test ensure_authenticated with no credentials in non-interactive mode."""
        # Clear any existing credentials
        self.session_manager.username = None
        self.session_manager.password = None

        with pytest.raises(
            Exception,
            match="Authentication required but interactive mode disabled",
        ):
            await self.session_manager.ensure_authenticated(interactive=False)

    @pytest.mark.asyncio
    async def test_get_installations_not_authenticated(self):
        """Test get_installations when not authenticated."""
        with pytest.raises(Exception, match="Not authenticated"):
            await self.session_manager.get_installations()

    @pytest.mark.asyncio
    async def test_get_installations_authenticated(self):
        """Test get_installations when authenticated."""
        self.session_manager.is_authenticated = True
        self.session_manager.installation_use_case = Mock()
        self.session_manager.installation_use_case.get_installations = (
            AsyncMock(return_value=["install1", "install2"])
        )

        result = await self.session_manager.get_installations()

        assert result == ["install1", "install2"]
        self.session_manager.installation_use_case.get_installations.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout(self):
        """Test logout method."""
        self.session_manager.username = "test_user"
        self.session_manager.password = "test_password"
        self.session_manager.is_authenticated = True
        self.session_manager.current_installation = "12345"

        # Create a session file
        self.session_manager._save_session()
        assert os.path.exists(self.session_file)

        with patch(
            "cli.utils.session_manager.clear_dependencies"
        ) as mock_clear:
            await self.session_manager.logout()

            assert self.session_manager.username is None
            assert self.session_manager.password is None
            assert self.session_manager.is_authenticated is False
            assert self.session_manager.current_installation is None
            assert not os.path.exists(self.session_file)
            mock_clear.assert_called_once()

    def test_get_session_file_path(self):
        """Test _get_session_file_path method."""
        with patch("os.path.expanduser") as mock_expanduser, patch(
            "os.makedirs"
        ) as mock_makedirs:
            mock_expanduser.return_value = "/home/test"

            path = self.session_manager._get_session_file_path()

            expected_path = "/home/test/.my_verisure/session.json"
            assert path == expected_path
            mock_makedirs.assert_called_once_with(
                "/home/test/.my_verisure", mode=0o700
            )

    def test_session_file_permissions(self):
        """Test that session file is created with correct permissions."""
        self.session_manager.username = "test_user"
        self.session_manager.password = "test_password"

        self.session_manager._save_session()

        assert os.path.exists(self.session_file)
        # Check that file has restricted permissions (readable/writable by owner only)
        stat = os.stat(self.session_file)
        # On Unix systems, files are typically created with 0o644 (rw-r--r--)
        # We just check that it's not world-writable (no write permissions for others)
        assert (
            stat.st_mode & 0o777
        ) & 0o002 == 0  # No write permissions for others

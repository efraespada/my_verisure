"""Integration tests for CLI."""

import pytest
import sys
import os
from unittest.mock import patch, Mock, AsyncMock
from io import StringIO

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from cli.main import main, create_parser, setup_logging


class TestCLIIntegration:
    """Integration tests for CLI."""

    def setup_method(self):
        """Set up test fixtures."""
        self.original_argv = sys.argv.copy()

    def teardown_method(self):
        """Clean up test fixtures."""
        sys.argv = self.original_argv

    def test_create_parser(self):
        """Test parser creation."""
        parser = create_parser()

        # Test that parser has expected subcommands
        subparsers = [
            action.dest
            for action in parser._actions
            if hasattr(action, "choices")
        ]
        assert len(subparsers) > 0

        # Test help
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            parser.print_help()
            help_output = mock_stdout.getvalue()
            assert "My Verisure CLI" in help_output
            assert "auth" in help_output
            assert "info" in help_output
            assert "alarm" in help_output

    def test_setup_logging(self):
        """Test logging setup."""
        with patch("logging.basicConfig") as mock_basic_config:
            setup_logging(verbose=True)
            mock_basic_config.assert_called_once()

    @pytest.mark.asyncio
    @patch("cli.main.AuthCommand")
    async def test_main_auth_login(self, mock_auth_command):
        """Test main function with auth login command."""
        sys.argv = ["my_verisure_cli.py", "auth", "login"]

        mock_command_instance = Mock()
        mock_command_instance.execute = AsyncMock(return_value=True)
        mock_auth_command.return_value = mock_command_instance

        with patch("cli.main.setup_logging"):
            result = await main()

        assert result == 0
        mock_command_instance.execute.assert_called_once_with(
            "login", interactive=True
        )

    @pytest.mark.asyncio
    @patch("cli.main.InfoCommand")
    async def test_main_info_installations(self, mock_info_command):
        """Test main function with info installations command."""
        sys.argv = ["my_verisure_cli.py", "info", "installations"]

        mock_command_instance = Mock()
        mock_command_instance.execute = AsyncMock(return_value=True)
        mock_info_command.return_value = mock_command_instance

        with patch("cli.main.setup_logging"):
            result = await main()

        assert result == 0
        mock_command_instance.execute.assert_called_once_with(
            "installations", interactive=True
        )

    @pytest.mark.asyncio
    @patch("cli.main.AlarmCommand")
    async def test_main_alarm_status(self, mock_alarm_command):
        """Test main function with alarm status command."""
        sys.argv = [
            "my_verisure_cli.py",
            "alarm",
            "status",
            "--installation-id",
            "12345",
        ]

        mock_command_instance = Mock()
        mock_command_instance.execute = AsyncMock(return_value=True)
        mock_alarm_command.return_value = mock_command_instance

        with patch("cli.main.setup_logging"):
            result = await main()

        assert result == 0
        mock_command_instance.execute.assert_called_once_with(
            "status", installation_id="12345", interactive=True
        )

    @pytest.mark.asyncio
    async def test_main_unknown_command(self):
        """Test main function with unknown command."""
        sys.argv = ["my_verisure_cli.py", "unknown"]

        with patch("cli.main.setup_logging"), patch(
            "sys.stderr", new_callable=StringIO
        ) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                await main()

        assert exc_info.value.code == 2  # ArgumentParser error exit code
        error_output = mock_stderr.getvalue()
        assert "error:" in error_output

    @pytest.mark.asyncio
    async def test_main_help(self):
        """Test main function with help command."""
        sys.argv = ["my_verisure_cli.py", "--help"]

        with patch("cli.main.setup_logging"), patch(
            "sys.stdout", new_callable=StringIO
        ) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await main()

        assert exc_info.value.code == 0
        help_output = mock_stdout.getvalue()
        assert "My Verisure CLI" in help_output
        assert "auth" in help_output
        assert "info" in help_output
        assert "alarm" in help_output

    @pytest.mark.asyncio
    @patch("cli.main.AuthCommand")
    async def test_main_command_failure(self, mock_auth_command):
        """Test main function when command fails."""
        sys.argv = ["my_verisure_cli.py", "auth", "login"]

        mock_command_instance = Mock()
        mock_command_instance.execute = AsyncMock(return_value=False)
        mock_auth_command.return_value = mock_command_instance

        with patch("cli.main.setup_logging"):
            result = await main()

        assert result == 1  # Error exit code
        mock_command_instance.execute.assert_called_once_with(
            "login", interactive=True
        )


class TestCLIArgumentParsing:
    """Test CLI argument parsing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = create_parser()

    def test_auth_subcommand_parsing(self):
        """Test auth subcommand argument parsing."""
        args = self.parser.parse_args(["auth", "login"])
        assert args.command == "auth"
        assert args.action == "login"

    def test_auth_logout_parsing(self):
        """Test auth logout argument parsing."""
        args = self.parser.parse_args(["auth", "logout"])
        assert args.command == "auth"
        assert args.action == "logout"

    def test_auth_status_parsing(self):
        """Test auth status argument parsing."""
        args = self.parser.parse_args(["auth", "status"])
        assert args.command == "auth"
        assert args.action == "status"

    def test_info_installations_parsing(self):
        """Test info installations argument parsing."""
        args = self.parser.parse_args(["info", "installations"])
        assert args.command == "info"
        assert args.action == "installations"

    def test_info_services_parsing(self):
        """Test info services argument parsing."""
        args = self.parser.parse_args(
            ["info", "services", "--installation-id", "12345"]
        )
        assert args.command == "info"
        assert args.action == "services"
        assert args.installation_id == "12345"

    def test_info_status_parsing(self):
        """Test info status argument parsing."""
        args = self.parser.parse_args(
            ["info", "status", "--installation-id", "12345"]
        )
        assert args.command == "info"
        assert args.action == "status"
        assert args.installation_id == "12345"

    def test_alarm_status_parsing(self):
        """Test alarm status argument parsing."""
        args = self.parser.parse_args(
            ["alarm", "status", "--installation-id", "12345"]
        )
        assert args.command == "alarm"
        assert args.action == "status"
        assert args.installation_id == "12345"

    def test_alarm_arm_parsing(self):
        """Test alarm arm argument parsing."""
        args = self.parser.parse_args(
            ["alarm", "arm", "--mode", "away", "--installation-id", "12345"]
        )
        assert args.command == "alarm"
        assert args.action == "arm"
        assert args.mode == "away"
        assert args.installation_id == "12345"

    def test_alarm_disarm_parsing(self):
        """Test alarm disarm argument parsing."""
        args = self.parser.parse_args(
            ["alarm", "disarm", "--installation-id", "12345"]
        )
        assert args.command == "alarm"
        assert args.action == "disarm"
        assert args.installation_id == "12345"

    def test_verbose_flag_parsing(self):
        """Test verbose flag parsing."""
        args = self.parser.parse_args(["--verbose", "auth", "status"])
        assert args.verbose is True
        assert args.command == "auth"
        assert args.action == "status"

    def test_non_interactive_flag_parsing(self):
        """Test non-interactive flag parsing."""
        args = self.parser.parse_args(["--non-interactive", "auth", "login"])
        assert args.non_interactive is True
        assert args.command == "auth"
        assert args.action == "login"


class TestCLIErrorHandling:
    """Test CLI error handling."""

    @pytest.mark.asyncio
    @patch("cli.main.AuthCommand")
    async def test_command_exception_handling(self, mock_auth_command):
        """Test handling of command exceptions."""
        sys.argv = ["my_verisure_cli.py", "auth", "login"]

        mock_command_instance = Mock()
        mock_command_instance.execute = AsyncMock(
            side_effect=Exception("Test error")
        )
        mock_auth_command.return_value = mock_command_instance

        with patch("cli.main.setup_logging"), patch(
            "sys.stdout", new_callable=StringIO
        ) as mock_stdout:
            result = await main()

        assert result == 1
        output = mock_stdout.getvalue()
        assert "Test error" in output

    @pytest.mark.asyncio
    async def test_invalid_arguments_handling(self):
        """Test handling of invalid arguments."""
        sys.argv = ["my_verisure_cli.py", "auth", "invalid_action"]

        with patch("cli.main.setup_logging"), patch(
            "sys.stderr", new_callable=StringIO
        ) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                await main()

        assert exc_info.value.code == 2  # ArgumentParser error exit code
        error_output = mock_stderr.getvalue()
        assert "error:" in error_output

    @pytest.mark.asyncio
    async def test_missing_arguments_handling(self):
        """Test handling of missing arguments."""
        sys.argv = ["my_verisure_cli.py", "auth"]

        with patch("cli.main.setup_logging"), patch(
            "sys.stdout", new_callable=StringIO
        ) as mock_stdout:
            result = await main()

        assert result == 1  # Command execution failed
        output = mock_stdout.getvalue()
        assert "Acción de autenticación desconocida" in output

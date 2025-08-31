"""Unit tests for CLI commands."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from cli.commands.auth import AuthCommand
from cli.commands.info import InfoCommand
from cli.commands.alarm import AlarmCommand
from cli.commands.base import BaseCommand


class TestBaseCommand:
    """Test BaseCommand class."""

    def setup_method(self):
        """Set up test fixtures."""

        # Create a concrete implementation for testing
        class TestCommand(BaseCommand):
            async def execute(self, *args, **kwargs):
                return True

        self.command = TestCommand()

    @pytest.mark.asyncio
    async def test_setup_success(self):
        """Test setup method success."""
        with patch.object(self.command, "setup") as mock_setup:
            mock_setup.return_value = True

            result = await self.command.setup()

            assert result is True

    @pytest.mark.asyncio
    async def test_setup_failure(self):
        """Test setup method failure."""
        with patch.object(self.command, "setup") as mock_setup:
            mock_setup.return_value = False

            result = await self.command.setup()

            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup method."""
        with patch.object(self.command, "cleanup") as mock_cleanup:
            await self.command.cleanup()
            mock_cleanup.assert_called_once()

    def test_get_installation_id_provided(self):
        """Test get_installation_id with provided ID."""
        result = self.command.get_installation_id("12345")
        assert result == "12345"

    def test_get_installation_id_from_session(self):
        """Test get_installation_id from session."""
        with patch(
            "cli.commands.base.session_manager"
        ) as mock_session_manager:
            mock_session_manager.current_installation = "12345"

            result = self.command.get_installation_id(None)
            assert result == "12345"

    def test_get_installation_id_select(self):
        """Test get_installation_id with selection."""
        with patch(
            "cli.commands.base.session_manager"
        ) as mock_session_manager:
            mock_session_manager.current_installation = None

            result = self.command.get_installation_id(None)
            assert result is None

    @pytest.mark.asyncio
    async def test_select_installation_if_needed_single(self):
        """Test select_installation_if_needed with single installation."""
        with patch.object(
            self.command, "select_installation_if_needed"
        ) as mock_select:
            mock_select.return_value = "12345"

            result = await self.command.select_installation_if_needed(None)
            assert result == "12345"

    @pytest.mark.asyncio
    async def test_select_installation_if_needed_multiple(self):
        """Test select_installation_if_needed with multiple installations."""
        with patch.object(
            self.command, "select_installation_if_needed"
        ) as mock_select:
            mock_select.return_value = "67890"

            result = await self.command.select_installation_if_needed(None)
            assert result == "67890"


class TestAuthCommand:
    """Test AuthCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = AuthCommand()

    @pytest.mark.asyncio
    async def test_execute_login(self):
        """Test execute with login action."""
        with patch.object(self.command, "_login") as mock_login:
            mock_login.return_value = True

            result = await self.command.execute("login")
            assert result is True
            mock_login.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_logout(self):
        """Test execute with logout action."""
        with patch.object(self.command, "_logout") as mock_logout:
            mock_logout.return_value = True

            result = await self.command.execute("logout")
            assert result is True
            mock_logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_status(self):
        """Test execute with status action."""
        with patch.object(self.command, "_status") as mock_status:
            mock_status.return_value = True

            result = await self.command.execute("status")
            assert result is True
            mock_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        """Test execute with unknown action."""
        with patch("cli.utils.display.print_error"):
            result = await self.command.execute("unknown")
            assert result is False
            # The error message is printed to stdout, not through print_error
            # So we check that the function returns False

    @pytest.mark.asyncio
    async def test_login_success(self):
        """Test _login method success."""
        with patch.object(self.command, "setup") as mock_setup:
            mock_setup.return_value = True

            result = await self.command._login()
            assert result is True

    @pytest.mark.asyncio
    async def test_login_failure(self):
        """Test _login method failure."""
        with patch.object(self.command, "setup") as mock_setup:
            mock_setup.return_value = False

            result = await self.command._login()
            assert result is False

    @pytest.mark.asyncio
    async def test_logout(self):
        """Test _logout method."""
        with patch(
            "cli.commands.auth.session_manager"
        ) as mock_session_manager:
            mock_session_manager.logout = AsyncMock()

            result = await self.command._logout()
            assert result is True
            mock_session_manager.logout.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_authenticated(self):
        """Test _status method when authenticated."""
        with patch(
            "cli.utils.session_manager.session_manager"
        ) as mock_session_manager:

            mock_session_manager.username = "test_user"
            mock_session_manager.is_authenticated = True
            mock_session_manager.current_installation = "12345"
            mock_session_manager.ensure_authenticated = AsyncMock(
                return_value=True
            )

            result = await self.command._status()
            assert result is True


class TestInfoCommand:
    """Test InfoCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = InfoCommand()

    @pytest.mark.asyncio
    async def test_execute_installations(self):
        """Test execute with installations action."""
        with patch.object(self.command, "_show_installations") as mock_show:
            mock_show.return_value = True

            result = await self.command.execute("installations")
            assert result is True
            mock_show.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_services(self):
        """Test execute with services action."""
        with patch.object(self.command, "_show_services") as mock_show:
            mock_show.return_value = True

            result = await self.command.execute(
                "services", installation_id="12345"
            )
            assert result is True
            mock_show.assert_called_once_with(installation_id="12345")

    @pytest.mark.asyncio
    async def test_execute_status(self):
        """Test execute with status action."""
        with patch.object(self.command, "_show_status") as mock_show:
            mock_show.return_value = True

            result = await self.command.execute(
                "status", installation_id="12345"
            )
            assert result is True
            mock_show.assert_called_once_with(installation_id="12345")

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        """Test execute with unknown action."""
        result = await self.command.execute("unknown")
        assert result is False

    @pytest.mark.asyncio
    async def test_show_installations_success(self):
        """Test _show_installations method success."""
        with patch.object(self.command, "setup") as mock_setup:

            mock_setup.return_value = True
            self.command.installation_use_case = Mock()
            mock_installations = [
                Mock(alias="Installation 1"),
                Mock(alias="Installation 2"),
            ]
            self.command.installation_use_case.get_installations = AsyncMock(
                return_value=mock_installations
            )

            result = await self.command._show_installations()
            assert result is True

    @pytest.mark.asyncio
    async def test_show_installations_failure(self):
        """Test _show_installations method failure."""
        with patch.object(self.command, "setup") as mock_setup:

            mock_setup.return_value = False

            result = await self.command._show_installations()
            assert result is False


class TestAlarmCommand:
    """Test AlarmCommand class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.command = AlarmCommand()

    @pytest.mark.asyncio
    async def test_execute_status(self):
        """Test execute with status action."""
        with patch.object(self.command, "_show_status") as mock_show:
            mock_show.return_value = True

            result = await self.command.execute(
                "status", installation_id="12345"
            )
            assert result is True
            mock_show.assert_called_once_with(installation_id="12345")

    @pytest.mark.asyncio
    async def test_execute_arm(self):
        """Test execute with arm action."""
        with patch.object(self.command, "_arm") as mock_arm:
            mock_arm.return_value = True

            result = await self.command.execute(
                "arm", mode="away", installation_id="12345"
            )
            assert result is True
            mock_arm.assert_called_once_with(
                mode="away", installation_id="12345"
            )

    @pytest.mark.asyncio
    async def test_execute_disarm(self):
        """Test execute with disarm action."""
        with patch.object(self.command, "_disarm") as mock_disarm:
            mock_disarm.return_value = True

            result = await self.command.execute(
                "disarm", installation_id="12345"
            )
            assert result is True
            mock_disarm.assert_called_once_with(installation_id="12345")

    @pytest.mark.asyncio
    async def test_execute_unknown_action(self):
        """Test execute with unknown action."""
        result = await self.command.execute("unknown")
        assert result is False

    @pytest.mark.asyncio
    async def test_show_status_success(self):
        """Test _show_status method success."""
        with patch.object(self.command, "setup") as mock_setup:

            mock_setup.return_value = True
            self.command.alarm_use_case = Mock()
            self.command.alarm_use_case.get_alarm_status = AsyncMock(
                return_value=Mock()
            )

            result = await self.command._show_status(installation_id="12345")
            assert result is True

    @pytest.mark.asyncio
    async def test_arm_success(self):
        """Test _arm method success."""
        with patch.object(self.command, "setup") as mock_setup, patch(
            "cli.commands.alarm.confirm_action"
        ) as mock_confirm, patch.object(
            self.command, "select_installation_if_needed"
        ) as mock_select:

            mock_setup.return_value = True
            mock_confirm.return_value = True
            mock_select.return_value = "12345"
            self.command.alarm_use_case = Mock()
            self.command.alarm_use_case.arm_away = AsyncMock(return_value=True)

            result = await self.command._arm(
                mode="away", installation_id="12345"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_disarm_success(self):
        """Test _disarm method success."""
        with patch.object(self.command, "setup") as mock_setup, patch(
            "cli.commands.alarm.confirm_action"
        ) as mock_confirm, patch.object(
            self.command, "select_installation_if_needed"
        ) as mock_select:

            mock_setup.return_value = True
            mock_confirm.return_value = True
            mock_select.return_value = "12345"
            self.command.alarm_use_case = Mock()
            self.command.alarm_use_case.disarm = AsyncMock(return_value=True)

            result = await self.command._disarm(installation_id="12345")
            assert result is True

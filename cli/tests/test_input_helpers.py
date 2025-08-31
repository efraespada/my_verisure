"""Unit tests for CLI input helper functions."""

from unittest.mock import patch, Mock

from cli.utils.input_helpers import (
    get_user_credentials,
    select_phone,
    get_otp_code,
    select_installation,
    confirm_action,
)


class TestInputHelpers:
    """Test input helper functions."""

    @patch("builtins.input")
    @patch("getpass.getpass")
    def test_get_user_credentials(self, mock_getpass, mock_input):
        """Test get_user_credentials function."""
        mock_input.return_value = "test_user"
        mock_getpass.return_value = "test_password"

        username, password = get_user_credentials()

        assert username == "test_user"
        assert password == "test_password"
        mock_input.assert_called_once_with("📋 User ID (DNI/NIE): ")
        mock_getpass.assert_called_once_with("🔑 Contraseña: ")

    @patch("builtins.input")
    def test_select_phone_single_phone(self, mock_input):
        """Test select_phone with single phone."""
        phones = [{"id": "1", "name": "Test Phone"}]
        mock_input.return_value = "1"

        phone_id = select_phone(phones)

        assert phone_id == "1"
        mock_input.assert_called_once_with(
            "Selecciona el número de teléfono (1, 2, ...): "
        )

    @patch("builtins.input")
    def test_select_phone_multiple_phones(self, mock_input):
        """Test select_phone with multiple phones."""
        phones = [
            {"id": "1", "name": "Phone 1"},
            {"id": "2", "name": "Phone 2"},
        ]
        mock_input.return_value = "2"

        phone_id = select_phone(phones)

        assert phone_id == "2"
        mock_input.assert_called_once_with(
            "Selecciona el número de teléfono (1, 2, ...): "
        )

    @patch("builtins.input")
    def test_select_phone_invalid_input(self, mock_input):
        """Test select_phone with invalid input."""
        phones = [
            {"id": "1", "name": "Phone 1"},
            {"id": "2", "name": "Phone 2"},
        ]
        mock_input.side_effect = ["invalid", "3", "1"]

        phone_id = select_phone(phones)

        assert phone_id == "1"
        assert mock_input.call_count == 3

    @patch("builtins.input")
    def test_get_otp_code(self, mock_input):
        """Test get_otp_code function."""
        mock_input.return_value = "123456"

        otp_code = get_otp_code()

        assert otp_code == "123456"
        mock_input.assert_called_once_with("🔢 Código OTP: ")

    @patch("builtins.input")
    def test_get_otp_code_empty_input(self, mock_input):
        """Test get_otp_code with empty input followed by valid input."""
        mock_input.side_effect = ["", "123456"]

        otp_code = get_otp_code()

        assert otp_code == "123456"
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_select_installation_single_installation(self, mock_input):
        """Test select_installation with single installation."""
        installations = [Mock(alias="Test Installation", numinst="12345")]

        installation_id = select_installation(installations)

        assert installation_id == "12345"
        mock_input.assert_not_called()  # Should auto-select single installation

    @patch("builtins.input")
    def test_select_installation_multiple_installations(self, mock_input):
        """Test select_installation with multiple installations."""
        installations = [
            Mock(alias="Installation 1", numinst="12345"),
            Mock(alias="Installation 2", numinst="67890"),
        ]
        mock_input.return_value = "2"

        installation_id = select_installation(installations)

        assert installation_id == "67890"
        mock_input.assert_called_once_with(
            "Selecciona el número de instalación (1-2): "
        )

    @patch("builtins.input")
    def test_select_installation_invalid_input(self, mock_input):
        """Test select_installation with invalid input."""
        installations = [
            Mock(alias="Installation 1", numinst="12345"),
            Mock(alias="Installation 2", numinst="67890"),
        ]
        mock_input.side_effect = ["invalid", "99999", "1"]

        installation_id = select_installation(installations)

        assert installation_id == "12345"
        assert mock_input.call_count == 3

    @patch("builtins.input")
    def test_confirm_action_yes(self, mock_input):
        """Test confirm_action with yes."""
        mock_input.return_value = "y"

        result = confirm_action("Test action?")

        assert result is True
        mock_input.assert_called_once_with("Responde 'sí' o 'no' (s/n): ")

    @patch("builtins.input")
    def test_confirm_action_no(self, mock_input):
        """Test confirm_action with no."""
        mock_input.return_value = "n"

        result = confirm_action("Test action?")

        assert result is False
        mock_input.assert_called_once_with("Responde 'sí' o 'no' (s/n): ")

    @patch("builtins.input")
    def test_confirm_action_empty_input(self, mock_input):
        """Test confirm_action with empty input followed by valid input."""
        mock_input.side_effect = ["", "no"]

        result = confirm_action("Test action?")

        assert result is False
        assert mock_input.call_count == 2

    @patch("builtins.input")
    def test_confirm_action_uppercase_yes(self, mock_input):
        """Test confirm_action with uppercase yes."""
        mock_input.return_value = "Y"

        result = confirm_action("Test action?")

        assert result is True
        mock_input.assert_called_once_with("Responde 'sí' o 'no' (s/n): ")

    @patch("builtins.input")
    def test_confirm_action_uppercase_no(self, mock_input):
        """Test confirm_action with uppercase no."""
        mock_input.return_value = "N"

        result = confirm_action("Test action?")

        assert result is False
        mock_input.assert_called_once_with("Responde 'sí' o 'no' (s/n): ")

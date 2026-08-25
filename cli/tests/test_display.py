"""Unit tests for CLI display utilities."""

from io import StringIO
from unittest.mock import patch

from cli.utils.display import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_command_header,
    print_installation_info,
    print_alarm_status,
    print_services_info,
    print_separator,
)


class TestDisplayFunctions:
    """Test display utility functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.output = StringIO()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.output.close()

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_header(self, mock_stdout):
        """Test print_header function."""
        print_header("TEST HEADER")
        output = mock_stdout.getvalue()
        assert (
            "============================================================"
            in output
        )
        assert "🚀 TEST HEADER" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_success(self, mock_stdout):
        """Test print_success function."""
        print_success("Operation completed")
        output = mock_stdout.getvalue()
        assert "✅ Operation completed" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_error(self, mock_stdout):
        """Test print_error function."""
        print_error("Something went wrong")
        output = mock_stdout.getvalue()
        assert "❌ Something went wrong" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_info(self, mock_stdout):
        """Test print_info function."""
        print_info("This is information")
        output = mock_stdout.getvalue()
        assert "ℹ️  This is information" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_warning(self, mock_stdout):
        """Test print_warning function."""
        print_warning("This is a warning")
        output = mock_stdout.getvalue()
        assert "⚠️  This is a warning" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_command_header(self, mock_stdout):
        """Test print_command_header function."""
        print_command_header("AUTH", "Authentication management")
        output = mock_stdout.getvalue()
        assert "🚀 MY VERISURE CLI - AUTH" in output
        assert "ℹ️  Authentication management" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_installation_info(self, mock_stdout):
        """Test print_installation_info function."""

        # Mock installation object
        class MockInstallation:
            def __init__(self):
                self.alias = "Test Installation"
                self.numinst = "12345"
                self.type = "home"
                self.name = "John"
                self.surname = "Doe"
                self.address = "123 Test St"
                self.city = "Test City"
                self.postcode = "12345"
                self.phone = "123456789"
                self.email = "EMAIL_SENTINEL"
                self.role = "OWNER"

        installation = MockInstallation()
        print_installation_info(installation, 1)
        output = mock_stdout.getvalue()
        assert "1. 🏠 Instalación: Instalación 1" in output
        assert "Test Installation" not in output
        assert "🆔 Número: [REDACTED]" in output
        assert "👤 Propietario: [REDACTED]" in output
        assert "123 Test St" not in output
        assert "EMAIL_SENTINEL" not in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_alarm_status(self, mock_stdout):
        """Test print_alarm_status function."""

        # Mock alarm status object
        class MockAlarmStatus:
            def __init__(self):
                self.status = "OK"
                self.message = "No alarm"
                self.numinst = "12345"
                self.protom_response = "No alarm"
                self.protom_response_date = "2025-08-31T18:25:26Z"
                self.forced_armed = False

        status = MockAlarmStatus()
        print_alarm_status(status)
        output = mock_stdout.getvalue()
        assert "🚀 ESTADO DE LA ALARMA" in output
        assert "🛡️  Estado: OK" in output
        assert "📋 Mensaje: Estado de alarma recibido" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_services_info_success(self, mock_stdout):
        """Test print_services_info with successful data."""

        # Mock services data
        class MockService:
            def __init__(
                self,
                service_id,
                request,
                active=True,
                visible=True,
                is_premium=False,
                bde=False,
            ):
                self.id_service = service_id
                self.request = request
                self.active = active
                self.visible = visible
                self.is_premium = is_premium
                self.bde = bde

        class MockServicesData:
            def __init__(self):
                self.success = True
                self.services = [
                    MockService("11", "EST"),
                    MockService("31", "ARM"),
                    MockService("32", "DARM"),
                ]
                self.installation_data = {
                    "status": "OP",
                    "panel": "SDVFAST",
                    "sim": "123456789",
                    "role": "OWNER",
                    "instIbs": "12345",
                }
                self.capabilities = "test_capabilities"

        services_data = MockServicesData()
        print_services_info(services_data)
        output = mock_stdout.getvalue()
        assert "✅ Se encontraron 3 servicios" in output
        assert "📊 Estado: OP" in output
        assert "🛡️  Panel:" not in output
        assert "SDVFAST" not in output
        assert "📱 SIM:" not in output
        assert "123456789" not in output
        assert "🔧 IBS:" not in output
        assert "12345" not in output
        assert "🔐 Capacidades:" not in output
        assert "11" not in output
        assert "EST" not in output
        assert "31" not in output
        assert "ARM" not in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_services_info_failure(self, mock_stdout):
        """Test print_services_info with failed data."""

        class MockServicesData:
            def __init__(self):
                self.success = False
                self.message = "Error getting services"

        services_data = MockServicesData()
        print_services_info(services_data)
        output = mock_stdout.getvalue()
        assert "❌ Error obteniendo servicios" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_separator(self, mock_stdout):
        """Test print_separator function."""
        print_separator()
        output = mock_stdout.getvalue()
        assert "-" * 60 in output

"""Unit tests for LogManager."""

import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock
from contextlib import nullcontext
from ...log_manager import LogManager


class TestLogManager:
    """Test LogManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_manager = Mock()
        
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock file manager
        self.mock_file_manager = Mock()
        self.mock_file_manager.load_json.return_value = []
        self.mock_file_manager.save_json.return_value = True
        self.mock_file_manager.get_file_size.return_value = 1024

    def teardown_method(self):
        """Clean up after each test."""

    def test_log_manager_initialization(self):
        """Test LogManager initialization."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            assert log_manager._file_manager == self.mock_file_manager
            assert log_manager._log_file == "my_verisure_logs.json"
            assert log_manager._max_logs == 1000

    def test_log_event_success(self):
        """Test successful event logging."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_event("test", "Test message", {"key": "value"})
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the log entry structure
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert len(logs) == 1
            assert logs[0]["event_type"] == "test"
            assert logs[0]["message"] == "Test message"
            assert logs[0]["data"] == {"key": "value"}
            assert "timestamp" in logs[0]

    def test_log_event_failure(self):
        """Test event logging failure."""
        with nullcontext():
            # Mock save failure
            self.mock_file_manager.save_json.return_value = False
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_event("test", "Test message")
            
            assert result is False

    def test_log_event_with_existing_logs(self):
        """Test event logging with existing logs."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {
                    "timestamp": "2024-01-01T00:00:00",
                    "event_type": "old",
                    "message": "Old message",
                    "data": {}
                }
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_event("new", "New message")
            
            assert result is True
            
            # Verify both old and new logs are present
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert len(logs) == 2
            assert logs[0]["event_type"] == "old"
            assert logs[1]["event_type"] == "new"

    def test_log_event_max_logs_limit(self):
        """Test event logging with max logs limit."""
        with nullcontext():
            # Mock existing logs at the limit
            existing_logs = [
                {
                    "timestamp": "2024-01-01T00:00:00",
                    "event_type": "old",
                    "message": f"Old message {i}",
                    "data": {}
                }
                for i in range(1000)
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_event("new", "New message")
            
            assert result is True
            
            # Verify only the last 1000 logs are kept
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert len(logs) == 1000
            assert logs[-1]["event_type"] == "new"

    def test_log_auth_event(self):
        """Test authentication event logging."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_auth_event("login", "user123", True, "Success")
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the log entry
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert logs[0]["event_type"] == "auth"
            assert logs[0]["message"] == "Authentication login: user123"
            assert logs[0]["data"]["user"] == "user123"
            assert logs[0]["data"]["success"] is True
            assert logs[0]["data"]["details"] == "Success"

    def test_log_alarm_event(self):
        """Test alarm event logging."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_alarm_event("arm", "inst123", "ARMED", "Away mode")
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the log entry
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert logs[0]["event_type"] == "alarm"
            assert logs[0]["message"] == "Alarm arm: ARMED"
            assert logs[0]["data"]["installation_id"] == "inst123"
            assert logs[0]["data"]["status"] == "ARMED"
            assert logs[0]["data"]["details"] == "Away mode"

    def test_log_error(self):
        """Test error event logging."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            exception = ValueError("Test error")
            result = log_manager.log_error("validation", "Test error message", exception)
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the log entry
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert logs[0]["event_type"] == "error"
            assert logs[0]["message"] == "Error: Test error message"
            assert logs[0]["data"]["error_type"] == "validation"
            assert logs[0]["data"]["exception"] == "Test error"

    def test_log_api_call(self):
        """Test API call logging."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.log_api_call("/api/test", "GET", True, 1.5)
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_once()
            
            # Verify the log entry
            call_args = self.mock_file_manager.save_json.call_args
            logs = call_args[0][1]
            assert logs[0]["event_type"] == "api"
            assert logs[0]["message"] == "API call: GET /api/test"
            assert logs[0]["data"]["endpoint"] == "/api/test"
            assert logs[0]["data"]["method"] == "GET"
            assert logs[0]["data"]["success"] is True
            assert logs[0]["data"]["response_time"] == 1.5

    def test_get_logs_all(self):
        """Test getting all logs."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {"event_type": "auth", "message": "Auth message", "timestamp": "2024-01-01T00:00:00"},
                {"event_type": "alarm", "message": "Alarm message", "timestamp": "2024-01-01T00:01:00"},
                {"event_type": "error", "message": "Error message", "timestamp": "2024-01-01T00:02:00"}
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.get_logs()
            
            assert len(result) == 3
            assert result[0]["event_type"] == "auth"
            assert result[1]["event_type"] == "alarm"
            assert result[2]["event_type"] == "error"

    def test_get_logs_filtered(self):
        """Test getting filtered logs."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {"event_type": "auth", "message": "Auth message", "timestamp": "2024-01-01T00:00:00"},
                {"event_type": "alarm", "message": "Alarm message", "timestamp": "2024-01-01T00:01:00"},
                {"event_type": "error", "message": "Error message", "timestamp": "2024-01-01T00:02:00"}
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.get_logs("auth")
            
            assert len(result) == 1
            assert result[0]["event_type"] == "auth"

    def test_get_logs_with_limit(self):
        """Test getting logs with limit."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {"event_type": "test", "message": f"Message {i}", "timestamp": "2024-01-01T00:00:00"}
                for i in range(5)
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.get_logs(limit=3)
            
            assert len(result) == 3
            assert result[0]["message"] == "Message 2"  # Last 3 entries

    def test_get_recent_logs(self):
        """Test getting recent logs."""
        with nullcontext():
            # Mock logs with different timestamps
            now = datetime.now()
            existing_logs = [
                {
                    "event_type": "old",
                    "message": "Old message",
                    "timestamp": (now - timedelta(hours=25)).isoformat()
                },
                {
                    "event_type": "recent",
                    "message": "Recent message",
                    "timestamp": (now - timedelta(hours=1)).isoformat()
                }
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.get_recent_logs(24)
            
            assert len(result) == 1
            assert result[0]["event_type"] == "recent"

    def test_clear_logs(self):
        """Test clearing logs."""
        with nullcontext():
            log_manager = LogManager(file_manager=self.mock_file_manager)
            
            result = log_manager.clear_logs()
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_with("my_verisure_logs.json", [])

    def test_export_logs(self):
        """Test exporting logs."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {"event_type": "auth", "message": "Auth message"},
                {"event_type": "alarm", "message": "Alarm message"}
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.export_logs("exported_logs.json")
            
            assert result is True
            self.mock_file_manager.save_json.assert_called_with("exported_logs.json", existing_logs)

    def test_export_logs_filtered(self):
        """Test exporting filtered logs."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {"event_type": "auth", "message": "Auth message"},
                {"event_type": "alarm", "message": "Alarm message"}
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.export_logs("exported_logs.json", "auth")
            
            assert result is True
            # Should only export auth logs
            call_args = self.mock_file_manager.save_json.call_args
            exported_logs = call_args[0][1]
            assert len(exported_logs) == 1
            assert exported_logs[0]["event_type"] == "auth"

    def test_get_log_stats(self):
        """Test getting log statistics."""
        with nullcontext():
            # Mock existing logs
            existing_logs = [
                {"event_type": "auth", "message": "Auth message", "timestamp": "2024-01-01T00:00:00"},
                {"event_type": "auth", "message": "Auth message 2", "timestamp": "2024-01-01T00:01:00"},
                {"event_type": "alarm", "message": "Alarm message", "timestamp": "2024-01-01T00:02:00"}
            ]
            self.mock_file_manager.load_json.return_value = existing_logs
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.get_log_stats()
            
            assert result["total_logs"] == 3
            assert result["recent_logs"] == 0
            assert result["event_counts"]["auth"] == 2
            assert result["event_counts"]["alarm"] == 1
            assert result["file_size"] == 1024

    def test_get_log_stats_error(self):
        """Test getting log statistics when error occurs."""
        with nullcontext():
            # Mock error
            self.mock_file_manager.load_json.side_effect = Exception("File error")
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager.get_log_stats()
            
            assert result == {
                "total_logs": 0,
                "recent_logs": 0,
                "event_counts": {},
                "file_size": 1024,
            }

    def test_load_logs_error(self):
        """Test loading logs when error occurs."""
        with nullcontext():
            # Mock error
            self.mock_file_manager.load_json.side_effect = Exception("File error")
            
            log_manager = LogManager(file_manager=self.mock_file_manager)
            result = log_manager._load_logs()
            
            assert result == []

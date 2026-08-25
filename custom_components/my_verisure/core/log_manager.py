"""Log manager for My Verisure integration."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .file_manager import FileManager

_LOGGER = logging.getLogger(__name__)


class LogManager:
    """Manager for application logs using FileManager."""
    
    def __init__(self, file_manager: FileManager):
        """Initialize the log manager with entry-scoped storage."""
        self._file_manager = file_manager
        self._log_file = "my_verisure_logs.json"
        self._max_logs = 1000  # Maximum number of logs to keep

    def _resolve_file_manager(self) -> FileManager:
        """Return the file manager owned by this composition root."""
        return self._file_manager
    
    def log_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Log a bounded, non-sensitive event projection."""
        try:
            safe_data = {
                key: value
                for key, value in (data or {}).items()
                if key in {"success", "status", "response_time", "error_type", "method"}
                and isinstance(value, (bool, int, float, str))
            }
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "message": f"{event_type} event",
                "data": safe_data,
            }
            logs = self._load_logs()
            logs.append(log_entry)
            if len(logs) > self._max_logs:
                logs = logs[-self._max_logs:]
            success = self._resolve_file_manager().save_json(self._log_file, logs)
            if success:
                _LOGGER.debug("Event logged: %s", event_type)
            return success
        except Exception:
            _LOGGER.error("Failed to log event")
            return False
    
    def log_auth_event(self, event: str, user: str, success: bool, details: Optional[str] = None) -> bool:
        """Log authentication events."""
        data = {"success": success}
        return self.log_event("auth", "Authentication event", data)
    
    def log_alarm_event(self, event: str, installation_id: str, status: str, details: Optional[str] = None) -> bool:
        """Log alarm events."""
        data = {"status": status}
        return self.log_event("alarm", "Alarm event", data)
    
    def log_error(self, error_type: str, message: str, exception: Optional[Exception] = None) -> bool:
        """Log error events."""
        data = {"error_type": error_type}
        return self.log_event("error", "Error event", data)
    
    def log_api_call(self, endpoint: str, method: str, success: bool, response_time: Optional[float] = None) -> bool:
        """Log API calls."""
        data = {"method": method, "success": success, "response_time": response_time}
        return self.log_event("api", "API event", data)
    
    def get_logs(self, event_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get logs, optionally filtered by event type."""
        try:
            logs = self._load_logs()
            
            # Filter by event type if specified
            if event_type:
                logs = [log for log in logs if log.get("event_type") == event_type]
            
            # Limit results if specified
            if limit:
                logs = logs[-limit:]
            
            return logs
        except Exception:
            _LOGGER.error("Failed to get logs")
            return []
    
    def get_recent_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get logs from the last N hours."""
        try:
            from datetime import datetime, timedelta
            
            logs = self._load_logs()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_logs = []
            for log in logs:
                try:
                    log_time = datetime.fromisoformat(log.get("timestamp", ""))
                    if log_time >= cutoff_time:
                        recent_logs.append(log)
                except ValueError:
                    # Skip logs with invalid timestamps
                    continue
            
            return recent_logs
        except Exception:
            _LOGGER.error("Failed to get recent logs")
            return []
    
    def clear_logs(self) -> bool:
        """Clear all logs."""
        try:
            success = self._resolve_file_manager().save_json(self._log_file, [])
            if success:
                _LOGGER.info("All logs cleared")
            return success
        except Exception:
            _LOGGER.error("Failed to clear logs")
            return False
    
    def export_logs(self, filename: str, event_type: Optional[str] = None) -> bool:
        """Export logs to a specific file."""
        try:
            logs = self.get_logs(event_type)
            return self._resolve_file_manager().save_json(filename, logs)
        except Exception:
            _LOGGER.error("Failed to export logs")
            return False
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics."""
        try:
            logs = self._load_logs()
            
            # Count by event type
            event_counts: Dict[str, int] = {}
            for log in logs:
                event_type = log.get("event_type", "unknown")
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Get recent activity (last 24 hours)
            recent_logs = self.get_recent_logs(24)
            
            return {
                "total_logs": len(logs),
                "recent_logs": len(recent_logs),
                "event_counts": event_counts,
                "file_size": self._resolve_file_manager().get_file_size(self._log_file)
            }
        except Exception:
            _LOGGER.error("Failed to get log stats")
            return {"error": "Log statistics unavailable"}
    
    def _load_logs(self) -> List[Dict[str, Any]]:
        """Load logs from file."""
        try:
            logs = self._resolve_file_manager().load_json(self._log_file)
            if not isinstance(logs, list):
                _LOGGER.error("Log file has invalid format")
                return []
            return [entry for entry in logs if isinstance(entry, dict)]
        except Exception:
            _LOGGER.error("Failed to load logs")
            return []

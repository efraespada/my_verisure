"""Log manager for My Verisure integration."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .file_manager import get_file_manager

_LOGGER = logging.getLogger(__name__)


class LogManager:
    """Manager for application logs using FileManager."""
    
    def __init__(self):
        """Initialize the log manager."""
        self._file_manager = get_file_manager()
        self._log_file = "my_verisure_logs.json"
        self._max_logs = 1000  # Maximum number of logs to keep
    
    def log_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> bool:
        """Log an event to the log file."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "message": message,
                "data": data or {}
            }
            
            # Load existing logs
            logs = self._load_logs()
            
            # Add new log entry
            logs.append(log_entry)
            
            # Keep only the last max_logs entries
            if len(logs) > self._max_logs:
                logs = logs[-self._max_logs:]
            
            # Save logs
            success = self._file_manager.save_json(self._log_file, logs)
            if success:
                _LOGGER.debug("Event logged: %s - %s", event_type, message)
            return success
        except Exception as e:
            _LOGGER.error("Failed to log event: %s", e)
            return False
    
    def log_auth_event(self, event: str, user: str, success: bool, details: Optional[str] = None) -> bool:
        """Log authentication events."""
        data = {
            "user": user,
            "success": success,
            "details": details
        }
        return self.log_event("auth", f"Authentication {event}: {user}", data)
    
    def log_alarm_event(self, event: str, installation_id: str, status: str, details: Optional[str] = None) -> bool:
        """Log alarm events."""
        data = {
            "installation_id": installation_id,
            "status": status,
            "details": details
        }
        return self.log_event("alarm", f"Alarm {event}: {status}", data)
    
    def log_error(self, error_type: str, message: str, exception: Optional[Exception] = None) -> bool:
        """Log error events."""
        data = {
            "error_type": error_type,
            "exception": str(exception) if exception else None
        }
        return self.log_event("error", f"Error: {message}", data)
    
    def log_api_call(self, endpoint: str, method: str, success: bool, response_time: Optional[float] = None) -> bool:
        """Log API calls."""
        data = {
            "endpoint": endpoint,
            "method": method,
            "success": success,
            "response_time": response_time
        }
        return self.log_event("api", f"API call: {method} {endpoint}", data)
    
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
        except Exception as e:
            _LOGGER.error("Failed to get logs: %s", e)
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
        except Exception as e:
            _LOGGER.error("Failed to get recent logs: %s", e)
            return []
    
    def clear_logs(self) -> bool:
        """Clear all logs."""
        try:
            success = self._file_manager.save_json(self._log_file, [])
            if success:
                _LOGGER.info("All logs cleared")
            return success
        except Exception as e:
            _LOGGER.error("Failed to clear logs: %s", e)
            return False
    
    def export_logs(self, filename: str, event_type: Optional[str] = None) -> bool:
        """Export logs to a specific file."""
        try:
            logs = self.get_logs(event_type)
            return self._file_manager.save_json(filename, logs)
        except Exception as e:
            _LOGGER.error("Failed to export logs: %s", e)
            return False
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics."""
        try:
            logs = self._load_logs()
            
            # Count by event type
            event_counts = {}
            for log in logs:
                event_type = log.get("event_type", "unknown")
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Get recent activity (last 24 hours)
            recent_logs = self.get_recent_logs(24)
            
            return {
                "total_logs": len(logs),
                "recent_logs": len(recent_logs),
                "event_counts": event_counts,
                "file_size": self._file_manager.get_file_size(self._log_file)
            }
        except Exception as e:
            _LOGGER.error("Failed to get log stats: %s", e)
            return {"error": str(e)}
    
    def _load_logs(self) -> List[Dict[str, Any]]:
        """Load logs from file."""
        try:
            logs = self._file_manager.load_json(self._log_file)
            return logs if logs is not None else []
        except Exception as e:
            _LOGGER.error("Failed to load logs: %s", e)
            return []


# Global instance
_log_manager_instance: Optional[LogManager] = None


def get_log_manager() -> LogManager:
    """Get the global log manager instance."""
    global _log_manager_instance
    if _log_manager_instance is None:
        _log_manager_instance = LogManager()
    return _log_manager_instance


def reset_log_manager() -> None:
    """Reset the global log manager instance."""
    global _log_manager_instance
    _log_manager_instance = None

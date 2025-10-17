"""Configuration manager for My Verisure integration."""

import logging
from typing import Any, Dict, Optional

from .file_manager import get_file_manager

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    """Manager for configuration data using FileManager."""
    
    def __init__(self):
        """Initialize the configuration manager."""
        self._file_manager = get_file_manager()
        self._config_file = "my_verisure_config.json"
        self._default_config = {
            "version": "1.0.0",
            "debug": False,
            "timeout": 30,
            "retry_attempts": 3,
            "cache_duration": 300,  # 5 minutes
            "features": {
                "alarm": True,
                "sensors": True,
                "cameras": False
            },
            "notifications": {
                "enabled": True,
                "alarm_events": True,
                "sensor_events": False
            },
            "auto_arm_perimeter_with_internal": False
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        try:
            config = self._file_manager.load_json(self._config_file)
            if config is None:
                _LOGGER.info("No config file found, using defaults")
                return self._default_config.copy()
            
            # Merge with defaults to ensure all keys exist
            merged_config = self._default_config.copy()
            merged_config.update(config)
            return merged_config
        except Exception as e:
            _LOGGER.error("Failed to load config: %s", e)
            return self._default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            # Add metadata
            config_with_meta = {
                "metadata": {
                    "saved_at": self._get_timestamp(),
                    "version": "1.0.0"
                },
                "config": config
            }
            
            success = self._file_manager.save_json(self._config_file, config_with_meta)
            if success:
                _LOGGER.info("Configuration saved successfully")
            return success
        except Exception as e:
            _LOGGER.error("Failed to save config: %s", e)
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values."""
        try:
            current_config = self.get_config()
            current_config.update(updates)
            return self.save_config(current_config)
        except Exception as e:
            _LOGGER.error("Failed to update config: %s", e)
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        config = self.get_config()
        return config.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value."""
        return self.update_config({key: value})
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        try:
            return self.save_config(self._default_config)
        except Exception as e:
            _LOGGER.error("Failed to reset config to defaults: %s", e)
            return False
    
    def export_config(self, filename: str) -> bool:
        """Export configuration to a specific file."""
        try:
            config = self.get_config()
            return self._file_manager.save_json(filename, config)
        except Exception as e:
            _LOGGER.error("Failed to export config: %s", e)
            return False
    
    def import_config(self, filename: str) -> bool:
        """Import configuration from a specific file."""
        try:
            config = self._file_manager.load_json(filename)
            if config is None:
                _LOGGER.error("Config file not found: %s", filename)
                return False
            
            return self.save_config(config)
        except Exception as e:
            _LOGGER.error("Failed to import config: %s", e)
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration metadata and info."""
        try:
            config_data = self._file_manager.load_json(self._config_file)
            if config_data is None:
                return {
                    "exists": False,
                    "using_defaults": True,
                    "file_path": str(self._file_manager.get_file_path(self._config_file))
                }
            
            metadata = config_data.get("metadata", {})
            return {
                "exists": True,
                "using_defaults": False,
                "file_path": str(self._file_manager.get_file_path(self._config_file)),
                "saved_at": metadata.get("saved_at"),
                "version": metadata.get("version"),
                "file_size": self._file_manager.get_file_size(self._config_file)
            }
        except Exception as e:
            _LOGGER.error("Failed to get config info: %s", e)
            return {"error": str(e)}


# Global instance
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance


def reset_config_manager() -> None:
    """Reset the global configuration manager instance."""
    global _config_manager_instance
    _config_manager_instance = None

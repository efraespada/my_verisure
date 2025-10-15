"""File manager for My Verisure integration."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

_LOGGER = logging.getLogger(__name__)


class FileManager:
    """Manager for file operations within the My Verisure project."""
    
    def __init__(self):
        """Initialize the file manager."""
        self._project_root = self._detect_project_root()
        self._data_dir = self._project_root / "data"
        self._ensure_data_directory()
    
    def _detect_project_root(self) -> Path:
        """Detect the project root directory based on execution context."""
        current_dir = Path.cwd()
        
        # Check if we're in a Home Assistant environment
        if "homeassistant" in str(current_dir).lower():
            # Running from Home Assistant
            _LOGGER.info("Detected Home Assistant environment")
            return current_dir / "custom_components" / "my_verisure"
        
        # Check if we're in the CLI project directory
        if (current_dir / "custom_components" / "my_verisure").exists():
            # Running from CLI project root
            _LOGGER.info("Detected CLI project environment")
            return current_dir / "custom_components" / "my_verisure"
        
        # Fallback: assume we're in the project root and look for custom_components
        project_root = current_dir
        while project_root != project_root.parent:
            if (project_root / "custom_components" / "my_verisure").exists():
                _LOGGER.info("Found project root: %s", project_root)
                return project_root / "custom_components" / "my_verisure"
            project_root = project_root.parent
        
        # Last resort: use current directory
        _LOGGER.warning("Could not detect project root, using current directory: %s", current_dir)
        return current_dir
    
    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            _LOGGER.info("Data directory ensured: %s", self._data_dir)
        except Exception as e:
            _LOGGER.error("Failed to create data directory: %s", e)
            raise
    
    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root
    
    def get_data_directory(self) -> Path:
        """Get the data directory path."""
        return self._data_dir
    
    def save_text(self, filename: str, content: str) -> bool:
        """Save text content to a file."""
        try:
            file_path = self._data_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            _LOGGER.info("Text saved to: %s", file_path)
            return True
        except Exception as e:
            _LOGGER.error("Failed to save text to %s: %s", filename, e)
            return False
    
    def load_text(self, filename: str) -> Optional[str]:
        """Load text content from a file."""
        try:
            file_path = self._data_dir / filename
            if not file_path.exists():
                _LOGGER.warning("File not found: %s", file_path)
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            _LOGGER.info("Text loaded from: %s", file_path)
            return content
        except Exception as e:
            _LOGGER.error("Failed to load text from %s: %s", filename, e)
            return None
    
    def save_json(self, filename: str, data: Union[Dict[str, Any], list]) -> bool:
        """Save JSON data to a file."""
        try:
            file_path = self._data_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            _LOGGER.info("JSON saved to: %s", file_path)
            return True
        except Exception as e:
            _LOGGER.error("Failed to save JSON to %s: %s", filename, e)
            return False
    
    def load_json(self, filename: str) -> Optional[Union[Dict[str, Any], list]]:
        """Load JSON data from a file."""
        try:
            file_path = self._data_dir / filename
            if not file_path.exists():
                _LOGGER.warning("File not found: %s", file_path)
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _LOGGER.info("JSON loaded from: %s", file_path)
            return data
        except Exception as e:
            _LOGGER.error("Failed to load JSON from %s: %s", filename, e)
            return None
    
    def file_exists(self, filename: str) -> bool:
        """Check if a file exists."""
        file_path = self._data_dir / filename
        return file_path.exists()
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file."""
        try:
            file_path = self._data_dir / filename
            if file_path.exists():
                file_path.unlink()
                _LOGGER.info("File deleted: %s", file_path)
                return True
            else:
                _LOGGER.warning("File not found for deletion: %s", file_path)
                return False
        except Exception as e:
            _LOGGER.error("Failed to delete file %s: %s", filename, e)
            return False
    
    def save_binary(self, filepath: str, content: bytes) -> bool:
        """Save binary content to a file."""
        try:
            # Create full path including subdirectories
            full_path = self._data_dir / filepath
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(content)
            _LOGGER.info("Binary data saved to: %s", full_path)
            return True
        except Exception as e:
            _LOGGER.error("Failed to save binary data to %s: %s", filepath, e)
            return False
    
    def save_base64_image(self, filepath: str, base64_content: str) -> bool:
        """Save base64 encoded image to a file."""
        try:
            import base64
            # Decode base64 content
            image_data = base64.b64decode(base64_content)
            return self.save_binary(filepath, image_data)
        except Exception as e:
            _LOGGER.error("Failed to save base64 image to %s: %s", filepath, e)
            return False
    
    def list_files(self, pattern: str = "*") -> list[str]:
        """List files in the data directory matching a pattern."""
        try:
            files = []
            for file_path in self._data_dir.glob(pattern):
                if file_path.is_file():
                    files.append(file_path.name)
            _LOGGER.info("Found %d files matching pattern '%s'", len(files), pattern)
            return files
        except Exception as e:
            _LOGGER.error("Failed to list files with pattern '%s': %s", pattern, e)
            return []
    
    def get_file_path(self, filename: str) -> Path:
        """Get the full path to a file."""
        return self._data_dir / filename
    
    def get_file_size(self, filename: str) -> Optional[int]:
        """Get the size of a file in bytes."""
        try:
            file_path = self._data_dir / filename
            if file_path.exists():
                return file_path.stat().st_size
            return None
        except Exception as e:
            _LOGGER.error("Failed to get file size for %s: %s", filename, e)
            return None


# Global instance
_file_manager_instance: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get the global file manager instance."""
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = FileManager()
    return _file_manager_instance


def reset_file_manager() -> None:
    """Reset the global file manager instance."""
    global _file_manager_instance
    _file_manager_instance = None

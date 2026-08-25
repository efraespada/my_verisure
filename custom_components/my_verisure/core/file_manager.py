"""File manager for My Verisure integration."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


async def _to_thread(func: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Run a blocking callable in the default executor (non-blocking for the event loop)."""
    return await asyncio.to_thread(func, *args, **kwargs)


class FileManager:
    """Manager for file operations within the My Verisure project."""
    
    def __init__(self, project_root: Path):
        """Initialize an entry-scoped file manager.

        The caller must supply the lifecycle-owned root; filesystem discovery is
        deliberately forbidden so one entry cannot leak into another.
        """
        if not isinstance(project_root, Path):
            raise TypeError("project_root must be an explicit Path")
        self._project_root = project_root
        self._data_dir = self._project_root / "data"

    def _safe_data_path(self, filename: str) -> Path:
        """Resolve a relative data path and reject traversal or symlink escapes."""
        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("data filename required")
        data_root = self._data_dir.resolve()
        candidate = (self._data_dir / filename).resolve()
        try:
            candidate.relative_to(data_root)
        except ValueError as exc:
            raise ValueError("data path escapes entry directory") from exc
        return candidate

    def _detect_project_root(self) -> Path:
        """Retained only as a fail-closed compatibility guard."""
        raise RuntimeError("project_root must be injected explicitly")
    
    def _ensure_data_directory(self) -> None:
        """Ensure the data directory exists."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            _LOGGER.info("Data directory ensured")
        except Exception:
            _LOGGER.error("Failed to create data directory")
            raise
    
    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return self._project_root

    def _cleanup_project_root_sync(self) -> bool:
        """Remove an owned temporary project root idempotently."""
        shutil.rmtree(self._project_root, ignore_errors=True)
        return not self._project_root.exists()

    async def async_cleanup_project_root(self) -> bool:
        """Remove an owned project root without blocking the event loop."""
        return await _to_thread(self._cleanup_project_root_sync)
    
    def get_data_directory(self) -> Path:
        """Get the data directory path."""
        return self._data_dir
    
    def save_text(self, filename: str, content: str) -> bool:
        """Save text content to a file (blocking I/O; prefer async_save_text from async code)."""
        try:
            self._ensure_data_directory()
            file_path = self._safe_data_path(filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            _LOGGER.info("Text saved")
            return True
        except Exception:
            _LOGGER.error("Failed to save text")
            return False
    
    def load_text(self, filename: str) -> Optional[str]:
        """Load text content from a file (blocking I/O; prefer async_load_text from async code)."""
        try:
            self._ensure_data_directory()
            file_path = self._safe_data_path(filename)
            if not file_path.exists():
                _LOGGER.warning("File not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            _LOGGER.info("Text loaded")
            return content
        except Exception:
            _LOGGER.error("Failed to load text")
            return None
    
    def save_json(self, filename: str, data: Union[Dict[str, Any], list]) -> bool:
        """Save JSON data to a file (blocking I/O; prefer async_save_json from async code)."""
        try:
            self._ensure_data_directory()
            file_path = self._safe_data_path(filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            _LOGGER.info("JSON saved")
            return True
        except Exception:
            _LOGGER.error("Failed to save JSON")
            return False
    
    def load_json(self, filename: str) -> Optional[Union[Dict[str, Any], list]]:
        """Load JSON data from a file (blocking I/O; prefer async_load_json from async code)."""
        try:
            self._ensure_data_directory()
            file_path = self._safe_data_path(filename)
            if not file_path.exists():
                _LOGGER.warning("File not found")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _LOGGER.info("JSON loaded")
            return data
        except Exception:
            _LOGGER.error("Failed to load JSON")
            return None
    
    def file_exists(self, filename: str) -> bool:
        """Check if a file exists."""
        file_path = self._safe_data_path(filename)
        return file_path.exists()
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file (blocking I/O; prefer async_delete_file from async code)."""
        try:
            self._ensure_data_directory()
            file_path = self._safe_data_path(filename)
            if file_path.exists():
                file_path.unlink()
                _LOGGER.info("File deleted")
                return True
            else:
                _LOGGER.warning("File not found for deletion")
                return False
        except Exception:
            _LOGGER.error("Failed to delete file")
            return False
    
    def delete_files_by_prefix(self, prefix: str) -> int:
        """Delete all files that start with the given prefix (blocking I/O; prefer async_delete_files_by_prefix)."""
        deleted_count = 0
        try:
            if not self._data_dir.exists():
                _LOGGER.warning("Data directory does not exist")
                return 0
            
            # Find all files that start with the prefix
            for file_path in self._data_dir.iterdir():
                if file_path.is_file() and file_path.name.startswith(prefix):
                    try:
                        file_path.unlink()
                        _LOGGER.info("File deleted")
                        deleted_count += 1
                    except Exception:
                        _LOGGER.error("Failed to delete file")
            
            if deleted_count > 0:
                _LOGGER.info("Deleted %d files with prefix '%s'", deleted_count, prefix)
            else:
                _LOGGER.info("No files found with prefix '%s'", prefix)
                
            return deleted_count
            
        except Exception:
            _LOGGER.error("Failed to delete files with prefix")
            return deleted_count
    
    def save_binary(self, filepath: str, content: bytes) -> bool:
        """Atomically save binary content (blocking I/O)."""
        temporary_path: Optional[Path] = None
        try:
            full_path = self._safe_data_path(filepath)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=full_path.parent,
                prefix=f".{full_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(content)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, full_path)
            temporary_path = None
            _LOGGER.info("Binary data saved")
            return True
        except Exception:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass
            _LOGGER.error("Failed to save binary data")
            return False
    
    def save_base64_image(self, filepath: str, base64_content: str) -> bool:
        """Save base64 encoded image to a file."""
        try:
            import base64
            # Decode base64 content
            image_data = base64.b64decode(base64_content)
            return self.save_binary(filepath, image_data)
        except Exception:
            _LOGGER.error("Failed to save base64 image")
            return False
    
    def mark_camera_directory_complete(self, directory: str) -> bool:
        """Commit a camera directory after all expected images are present."""
        try:
            return self.save_binary(f"{directory}/.complete", b"complete")
        except Exception:
            _LOGGER.error("Failed to commit camera directory")
            return False

    def list_files(self, pattern: str = "*") -> list[str]:
        """List files in the data directory matching a pattern (blocking I/O; prefer async_list_files)."""
        try:
            files = []
            for file_path in self._data_dir.glob(pattern):
                if file_path.is_file():
                    files.append(file_path.name)
            _LOGGER.info("Found files matching requested pattern")
            return files
        except Exception:
            _LOGGER.error("Failed to list files")
            return []
    
    def get_file_path(self, filename: str) -> Path:
        """Get the full path to a file."""
        return self._safe_data_path(filename)
    
    def get_file_size(self, filename: str) -> Optional[int]:
        """Get the size of a file in bytes (blocking I/O; prefer async_get_file_size from async code)."""
        try:
            self._ensure_data_directory()
            file_path = self._safe_data_path(filename)
            if file_path.exists():
                return file_path.stat().st_size
            return None
        except Exception:
            _LOGGER.error("Failed to get file size")
            return None

    def _device_identifiers_path(self) -> Path:
        """Return the entry-scoped device identifier path."""
        return self._safe_data_path("device_identifiers.json")

    def save_device_identifiers(self, data: Dict[str, Any]) -> bool:
        """Save device identifiers in this entry's data directory."""
        try:
            self._ensure_data_directory()
            file_path = self._device_identifiers_path()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            _LOGGER.info("Device identifiers saved")
            return True
        except Exception:
            _LOGGER.error("Failed to save device identifiers")
            return False

    def load_device_identifiers(self) -> Optional[Dict[str, Any]]:
        """Load device identifiers from this entry's data directory."""
        try:
            self._ensure_data_directory()
            file_path = self._device_identifiers_path()
            if not file_path.exists():
                return None
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            _LOGGER.info("Device identifiers loaded")
            return data
        except Exception:
            _LOGGER.error("Failed to load device identifiers")
            return None

    def device_identifiers_exists(self) -> bool:
        """Check whether this entry has device identifiers."""
        return self._device_identifiers_path().exists()

    async def async_save_text(self, filename: str, content: str) -> bool:
        """Save text content to a file without blocking the event loop."""
        return await _to_thread(self.save_text, filename, content)

    async def async_load_text(self, filename: str) -> Optional[str]:
        """Load text content from a file without blocking the event loop."""
        return await _to_thread(self.load_text, filename)

    async def async_save_json(
        self, filename: str, data: Union[Dict[str, Any], list]
    ) -> bool:
        """Save JSON data to a file without blocking the event loop."""
        return await _to_thread(self.save_json, filename, data)

    async def async_load_json(
        self, filename: str
    ) -> Optional[Union[Dict[str, Any], list]]:
        """Load JSON data from a file without blocking the event loop."""
        return await _to_thread(self.load_json, filename)

    async def async_delete_file(self, filename: str) -> bool:
        """Delete a file without blocking the event loop."""
        return await _to_thread(self.delete_file, filename)

    async def async_delete_files_by_prefix(self, prefix: str) -> int:
        """Delete all files that start with the given prefix without blocking the event loop."""
        return await _to_thread(self.delete_files_by_prefix, prefix)

    async def async_save_binary(self, filepath: str, content: bytes) -> bool:
        """Save binary content to a file without blocking the event loop."""
        return await _to_thread(self.save_binary, filepath, content)

    async def async_list_files(self, pattern: str = "*") -> list[str]:
        """List files in the data directory matching a pattern without blocking the event loop."""
        return await _to_thread(self.list_files, pattern)

    async def async_get_file_size(self, filename: str) -> Optional[int]:
        """Get the size of a file in bytes without blocking the event loop."""
        return await _to_thread(self.get_file_size, filename)

    async def async_save_device_identifiers(self, data: Dict[str, Any]) -> bool:
        """Save device identifiers without blocking the event loop."""
        return await _to_thread(self.save_device_identifiers, data)

    async def async_load_device_identifiers(self) -> Optional[Dict[str, Any]]:
        """Load device identifiers without blocking the event loop."""
        return await _to_thread(self.load_device_identifiers)

    async def async_device_identifiers_exists(self) -> bool:
        """Check if device identifiers file exists without blocking the event loop."""
        return await _to_thread(self.device_identifiers_exists)

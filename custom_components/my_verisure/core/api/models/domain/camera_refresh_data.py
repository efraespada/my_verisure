"""
Domain models for camera refresh data.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class CameraRefreshData:
    """Domain model for camera refresh data."""
    
    timestamp: str
    num_images: int
    camera_identifier: str
    
    def __post_init__(self):
        """Validate the data after initialization."""
        if not self.timestamp:
            raise ValueError("Timestamp cannot be empty")
        if self.num_images < 0:
            raise ValueError("Number of images cannot be negative")
        if not self.camera_identifier:
            raise ValueError("Camera identifier cannot be empty")
    
    @classmethod
    def create(
        cls,
        timestamp: str,
        num_images: int,
        camera_identifier: str,
    ) -> "CameraRefreshData":
        """Create a new CameraRefreshData instance."""
        return cls(
            timestamp=timestamp,
            num_images=num_images,
            camera_identifier=camera_identifier,
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "num_images": self.num_images,
            "camera_identifier": self.camera_identifier,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CameraRefreshData":
        """Create from dictionary."""
        return cls(
            timestamp=data.get("timestamp", ""),
            num_images=data.get("num_images", 0),
            camera_identifier=data.get("camera_identifier", ""),
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"CameraRefreshData(camera={self.camera_identifier}, images={self.num_images}, timestamp={self.timestamp})"
    
    def __repr__(self) -> str:
        """Representation."""
        return self.__str__()

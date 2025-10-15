"""
Domain models for camera refresh operations.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

from .camera_refresh_data import CameraRefreshData


@dataclass
class CameraRefresh:
    """Domain model for camera refresh operation containing multiple camera refresh data."""
    
    refresh_data: List[CameraRefreshData]
    total_cameras: int
    successful_refreshes: int
    failed_refreshes: int
    timestamp: str
    
    def __post_init__(self):
        """Validate the data after initialization."""
        if not self.timestamp:
            raise ValueError("Timestamp cannot be empty")
        if self.total_cameras < 0:
            raise ValueError("Total cameras cannot be negative")
        if self.successful_refreshes < 0:
            raise ValueError("Successful refreshes cannot be negative")
        if self.failed_refreshes < 0:
            raise ValueError("Failed refreshes cannot be negative")
        if self.successful_refreshes + self.failed_refreshes != self.total_cameras:
            raise ValueError("Successful + failed refreshes must equal total cameras")
    
    @classmethod
    def create(
        cls,
        refresh_data: List[CameraRefreshData],
        timestamp: Optional[str] = None,
    ) -> "CameraRefresh":
        """Create a new CameraRefresh instance."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        total_cameras = len(refresh_data)
        successful_refreshes = sum(1 for data in refresh_data if data.num_images > 0)
        failed_refreshes = total_cameras - successful_refreshes
        
        return cls(
            refresh_data=refresh_data,
            total_cameras=total_cameras,
            successful_refreshes=successful_refreshes,
            failed_refreshes=failed_refreshes,
            timestamp=timestamp,
        )
    
    def add_refresh_data(self, data: CameraRefreshData) -> None:
        """Add a new camera refresh data to the list."""
        self.refresh_data.append(data)
        self.total_cameras += 1
        if data.num_images > 0:
            self.successful_refreshes += 1
        else:
            self.failed_refreshes += 1
    
    def get_successful_cameras(self) -> List[CameraRefreshData]:
        """Get only the successful camera refresh data."""
        return [data for data in self.refresh_data if data.num_images > 0]
    
    def get_failed_cameras(self) -> List[CameraRefreshData]:
        """Get only the failed camera refresh data."""
        return [data for data in self.refresh_data if data.num_images == 0]
    
    def get_camera_by_identifier(self, camera_identifier: str) -> Optional[CameraRefreshData]:
        """Get camera refresh data by identifier."""
        for data in self.refresh_data:
            if data.camera_identifier == camera_identifier:
                return data
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "refresh_data": [data.to_dict() for data in self.refresh_data],
            "total_cameras": self.total_cameras,
            "successful_refreshes": self.successful_refreshes,
            "failed_refreshes": self.failed_refreshes,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CameraRefresh":
        """Create from dictionary."""
        refresh_data = [
            CameraRefreshData.from_dict(item) 
            for item in data.get("refresh_data", [])
        ]
        
        return cls(
            refresh_data=refresh_data,
            total_cameras=data.get("total_cameras", 0),
            successful_refreshes=data.get("successful_refreshes", 0),
            failed_refreshes=data.get("failed_refreshes", 0),
            timestamp=data.get("timestamp", ""),
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"CameraRefresh(total={self.total_cameras}, successful={self.successful_refreshes}, failed={self.failed_refreshes}, timestamp={self.timestamp})"
    
    def __repr__(self) -> str:
        """Representation."""
        return self.__str__()

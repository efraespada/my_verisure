"""Camera Request Image DTOs for My Verisure API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class CameraRequestImageDTO:
    """DTO for camera image request."""
    
    success: bool
    reference_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraRequestImageDTO":
        """Create DTO from dictionary."""
        return cls(
            success=data.get("success", False),
            reference_id=data.get("reference_id"),
            message=data.get("message"),
            error=data.get("error"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            "success": self.success,
            "reference_id": self.reference_id,
            "message": self.message,
            "error": self.error,
        }


@dataclass
class CameraRequestImageStatusDTO:
    """DTO for camera status check."""
    
    success: bool
    status: Optional[str] = None
    counter: Optional[int] = None
    message: Optional[str] = None
    installation_id: Optional[str] = None
    error: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraRequestImageStatusDTO":
        """Create DTO from dictionary."""
        return cls(
            success=data.get("success", False),
            status=data.get("status"),
            counter=data.get("counter"),
            message=data.get("message"),
            installation_id=data.get("installation_id"),
            error=data.get("error"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            "success": self.success,
            "status": self.status,
            "counter": self.counter,
            "message": self.message,
            "installation_id": self.installation_id,
            "error": self.error,
        }


@dataclass
class CameraRequestImageResultDTO:
    """DTO for camera image result."""
    
    success: bool
    reference_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CameraRequestImageResultDTO":
        """Create DTO from dictionary."""
        return cls(
            success=data.get("success", False),
            reference_id=data.get("reference_id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            "success": self.success,
            "reference_id": self.reference_id,
        }

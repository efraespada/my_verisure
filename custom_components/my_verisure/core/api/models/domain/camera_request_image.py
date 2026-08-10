"""Pure camera image request domain models."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CameraRequestImage:
    success: bool
    reference_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class CameraRequestImageStatus:
    success: bool
    status: Optional[str] = None
    counter: Optional[int] = None
    message: Optional[str] = None
    installation_id: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class CameraRequestImageResult:
    success: bool
    successful_requests: int
    reference_id: Optional[str] = None

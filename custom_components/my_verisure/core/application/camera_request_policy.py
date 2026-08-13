"""Pure policies for camera request context and image storage paths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CameraRequestContext:
    """Headers and variables shared by camera GraphQL operations."""

    variables: dict[str, object]
    headers: dict[str, str] | None


class CameraRequestPolicy:
    """Build protocol context without performing I/O."""

    def build_context(
        self,
        *,
        installation_id: str,
        panel: str,
        devices: list[int],
        capabilities: str,
        session_data: dict[str, object] | None,
        hash_token: str | None,
        header_factory,
    ) -> CameraRequestContext:
        headers = (
            header_factory(session_data, hash_token) if session_data else None
        )
        if headers is not None:
            headers.update(
                {
                    "numinst": installation_id,
                    "panel": panel,
                    "x-capabilities": capabilities,
                }
            )
        return CameraRequestContext(
            variables={"numinst": installation_id, "panel": panel, "devices": devices},
            headers=headers,
        )

    @staticmethod
    def image_directory(timestamp: str, now: datetime | None = None) -> str:
        normalized = timestamp.replace(" ", "_").replace(":", "-").replace("/", "-")
        if normalized:
            return normalized
        return (now or datetime.now()).strftime("%Y-%m-%d_%H-%M-%S")

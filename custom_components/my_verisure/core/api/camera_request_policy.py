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
        if not session_data or not isinstance(hash_token, str) or not hash_token.strip():
            raise ValueError("authenticated session required")
        if (
            not isinstance(installation_id, str)
            or not installation_id.strip()
            or not isinstance(panel, str)
            or not panel.strip()
            or not isinstance(capabilities, str)
            or not capabilities.strip()
            or not devices
        ):
            raise ValueError("camera request context required")
        headers = header_factory(session_data, hash_token)
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
        if not normalized:
            raise ValueError("camera timestamp required")
        return normalized

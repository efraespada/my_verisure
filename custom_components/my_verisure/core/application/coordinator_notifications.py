"""Home Assistant notification effect boundary for the coordinator."""

from __future__ import annotations

from typing import Any, Protocol


class TranslationReader(Protocol):
    """Port for localized message lookup."""

    async def __call__(self, key: str, **kwargs: object) -> str:
        """Return a localized message."""
        ...


class NotificationCreator(Protocol):
    """Port for creating a persistent Home Assistant notification."""

    def __call__(self, message: str, *, title: str, notification_id: str) -> Any:
        """Create a notification."""


class CoordinatorNotificationService:
    """Translate and publish coordinator notifications."""

    def __init__(
        self,
        translate: TranslationReader,
        create: NotificationCreator,
    ) -> None:
        self._translate = translate
        self._create = create

    async def notify(
        self,
        *,
        title_key: str,
        message_key: str,
        notification_id: str,
        message_args: dict[str, object] | None = None,
    ) -> None:
        """Resolve title/message and create one persistent notification."""
        args = message_args or {}
        title = await self._translate(title_key)
        message = await self._translate(message_key, **args)
        self._create(message, title=title, notification_id=notification_id)

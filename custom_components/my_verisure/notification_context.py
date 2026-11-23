"""Carry an explicitly known HA action context without exposing it to the core.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from collections.abc import Callable, Coroutine
from contextvars import ContextVar
from functools import wraps
from typing import Any

from homeassistant.core import Context, ServiceCall

NOTIFICATION_CONTEXT: ContextVar[Context | None] = ContextVar(
    "my_verisure_notification_context", default=None
)


def notification_service_context(
    handler: Callable[[ServiceCall], Coroutine[Any, Any, None]],
) -> Callable[[ServiceCall], Coroutine[Any, Any, None]]:
    """Restore the previous context even when an action fails or is cancelled."""

    @wraps(handler)
    async def wrapped(call: ServiceCall) -> None:
        token = NOTIFICATION_CONTEXT.set(getattr(call, "context", None))
        try:
            await handler(call)
        finally:
            NOTIFICATION_CONTEXT.reset(token)

    return wrapped

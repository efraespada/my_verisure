"""Only explicit local HA action context propagates to synchronous results.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from types import SimpleNamespace

from homeassistant.core import Context
import pytest

from custom_components.my_verisure.notification_context import (
    NOTIFICATION_CONTEXT,
    notification_service_context,
)


@pytest.mark.parametrize("outcome", ["success", "failure", "cancel"])
async def test_known_context_is_restored_on_every_handler_exit(outcome):
    previous, local = Context(), Context(user_id="synthetic-user")
    token = NOTIFICATION_CONTEXT.set(previous)

    @notification_service_context
    async def handler(call):
        assert NOTIFICATION_CONTEXT.get() is local
        if outcome == "failure":
            raise ValueError
        if outcome == "cancel":
            raise asyncio.CancelledError

    try:
        if outcome == "success":
            await handler(SimpleNamespace(context=local))
        else:
            with pytest.raises(
                ValueError if outcome == "failure" else asyncio.CancelledError
            ):
                await handler(SimpleNamespace(context=local))
        assert NOTIFICATION_CONTEXT.get() is previous
    finally:
        NOTIFICATION_CONTEXT.reset(token)

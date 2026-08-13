"""Tests for coordinator notification effects."""

from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.coordinator_notifications import (
    CoordinatorNotificationService,
)


@pytest.mark.asyncio
async def test_notify_translates_both_parts_and_creates_notification() -> None:
    translate = AsyncMock(side_effect=["Error", "Failed: offline"])
    create = Mock()
    service = CoordinatorNotificationService(translate, create)

    await service.notify(
        title_key="notifications.title.error",
        message_key="notifications.error",
        notification_id="verisure_error",
        message_args={"message": "offline"},
    )

    assert translate.await_args_list[0].args == ("notifications.title.error",)
    assert translate.await_args_list[1].kwargs == {"message": "offline"}
    create.assert_called_once_with(
        "Failed: offline",
        title="Error",
        notification_id="verisure_error",
    )


@pytest.mark.asyncio
async def test_notify_uses_empty_args_by_default() -> None:
    translate = AsyncMock(side_effect=["Title", "Message"])
    create = Mock()

    await CoordinatorNotificationService(translate, create).notify(
        title_key="title",
        message_key="message",
        notification_id="id",
    )

    assert create.called

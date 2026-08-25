"""Tests for Home Assistant authentication transaction semantics."""

import asyncio
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.my_verisure.core.application.auth_flow_transactions import (
    AuthFlowTransactionService,
)


@pytest.mark.asyncio
async def test_rollback_clears_and_confirms_session_after_restore_failure():
    service = AuthFlowTransactionService()
    entry = SimpleNamespace(entry_id="entry", data={"value": "old"})
    session = cast(
        Any,
        SimpleNamespace(
            async_restore_transaction_state=AsyncMock(
                side_effect=RuntimeError("restore failed")
            ),
            async_clear_credentials=AsyncMock(),
            async_capture_transaction_state=AsyncMock(
                return_value=(
                    {
                        "username": None,
                        "password": None,
                        "hash_token": None,
                        "refresh_token": None,
                        "is_authenticated": False,
                    },
                    None,
                )
            ),
        ),
    )
    update_entry = Mock(side_effect=lambda target, *, data: setattr(target, "data", dict(data)))

    await service.rollback_reauthentication(
        entry=entry,
        previous_data={"value": "old"},
        session=session,
        session_snapshot={"username": "old"},
        session_bytes=b"old",
        update_entry=update_entry,
        reload_entry=AsyncMock(return_value=True),
        get_entry=lambda _entry_id: entry,
    )

    session.async_clear_credentials.assert_awaited_once()


@pytest.mark.asyncio
async def test_rollback_rejects_unconfirmed_fail_closed_cleanup():
    service = AuthFlowTransactionService()
    service.async_fail_closed_reauthentication = AsyncMock(return_value=False)

    with pytest.raises(RuntimeError, match="cleanup could not be confirmed"):
        await service.rollback_reauthentication(
            entry=SimpleNamespace(entry_id="entry", data={"value": "old"}),
            previous_data={"value": "old"},
            session=cast(Any, SimpleNamespace()),
            session_snapshot={"username": "old"},
            session_bytes=b"old",
            update_entry=Mock(),
            reload_entry=AsyncMock(return_value=True),
            get_entry=lambda _entry_id: None,
        )


@pytest.mark.asyncio
async def test_rollback_without_session_snapshot_clears_and_confirms_session():
    service = AuthFlowTransactionService()
    entry = SimpleNamespace(entry_id="entry", data={"value": "old"})
    session = cast(
        Any,
        SimpleNamespace(
            async_clear_credentials=AsyncMock(),
            async_capture_transaction_state=AsyncMock(
                return_value=(
                    {
                        "username": None,
                        "password": None,
                        "hash_token": None,
                        "refresh_token": None,
                        "is_authenticated": False,
                    },
                    None,
                )
            ),
        ),
    )

    await service.rollback_reauthentication(
        entry=entry,
        previous_data={"value": "old"},
        session=session,
        session_snapshot=None,
        session_bytes=None,
        update_entry=Mock(
            side_effect=lambda target, *, data: setattr(target, "data", dict(data))
        ),
        reload_entry=AsyncMock(return_value=True),
        get_entry=lambda _entry_id: entry,
    )

    session.async_clear_credentials.assert_awaited_once()




@pytest.mark.asyncio
async def test_commit_retries_entry_rollback_after_transient_update_failure():
    service = AuthFlowTransactionService()
    entry = SimpleNamespace(entry_id="entry", data={"value": "old"})
    calls = 0

    def update_entry(target, *, data):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("rollback persist failed")
        target.data = dict(data)

    reload_entry = AsyncMock(side_effect=[False, True])
    get_entry = lambda _entry_id: entry

    committed = await service.commit_reauthentication(
        entry=entry,
        updated_data={"value": "new"},
        previous_data={"value": "old"},
        session=cast(
            Any,
            SimpleNamespace(
                async_clear_credentials=AsyncMock(),
                async_capture_transaction_state=AsyncMock(
                    return_value=(
                        {
                            "username": None,
                            "password": None,
                            "hash_token": None,
                            "refresh_token": None,
                            "is_authenticated": False,
                        },
                        None,
                    )
                ),
            ),
        ),
        session_snapshot=None,
        session_bytes=None,
        update_entry=update_entry,
        reload_entry=reload_entry,
        get_entry=get_entry,
    )

    assert committed is False
    assert entry.data == {"value": "old"}


@pytest.mark.asyncio
async def test_commit_preserves_cancellation_when_rollback_fails():
    service = AuthFlowTransactionService()
    entry = SimpleNamespace(entry_id="entry", data={"value": "old"})
    reload_entry = AsyncMock(
        side_effect=[asyncio.CancelledError(), RuntimeError("rollback failed")]
    )

    def update_entry(target, *, data):
        target.data = dict(data)

    with pytest.raises(asyncio.CancelledError):
        await service.commit_reauthentication(
            entry=entry,
            updated_data={"value": "new"},
            previous_data={"value": "old"},
            session=cast(Any, SimpleNamespace()),
            session_snapshot=None,
            session_bytes=None,
            update_entry=update_entry,
            reload_entry=reload_entry,
            get_entry=lambda _entry_id: entry,
        )


@pytest.mark.asyncio
async def test_rollback_propagates_cancellation_from_session_restore():
    service = AuthFlowTransactionService()
    session = cast(
        Any,
        SimpleNamespace(
            async_restore_transaction_state=AsyncMock(side_effect=asyncio.CancelledError()),
            async_clear_credentials=AsyncMock(),
            async_capture_transaction_state=AsyncMock(
                return_value=(
                    {
                        "username": None,
                        "password": None,
                        "hash_token": None,
                        "refresh_token": None,
                        "is_authenticated": False,
                    },
                    None,
                )
            ),
        ),
    )

    with pytest.raises(asyncio.CancelledError):
        await service.rollback_reauthentication(
            entry=SimpleNamespace(entry_id="entry", data={"value": "old"}),
            previous_data={"value": "old"},
            session=session,
            session_snapshot={"username": "old"},
            session_bytes=b"old",
            update_entry=Mock(),
            reload_entry=AsyncMock(return_value=True),
            get_entry=lambda _entry_id: None,
        )

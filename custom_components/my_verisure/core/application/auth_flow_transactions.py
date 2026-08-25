"""Transactional storage policies used by the Home Assistant auth flow."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Protocol


class SessionTransactionPort(Protocol):
    """Session capabilities required by the configuration-flow transaction."""

    async def async_capture_transaction_state(self) -> tuple[dict[str, object], bytes | None]: ...

    async def async_restore_transaction_state(
        self, snapshot: dict[str, object], previous_bytes: bytes | None
    ) -> None: ...

    async def async_clear_session_file(self) -> bool: ...

    async def async_clear_credentials(self) -> None: ...

    async def async_session_file_exists(self) -> bool: ...


class StorageCleanupPort(Protocol):
    """Entry-scoped storage cleanup capabilities."""

    async def async_cleanup_project_root(self) -> bool: ...

    async def async_device_identifiers_exists(self) -> bool: ...


UpdateEntry = Callable[..., Any]
ReloadEntry = Callable[[str], Awaitable[bool]]
GetEntry = Callable[[str], Any]


class AuthFlowTransactionService:
    """Own fail-closed cleanup and reauthentication transactions."""

    async def cleanup_initial_flow(
        self,
        storage: StorageCleanupPort,
        session: SessionTransactionPort | None,
    ) -> bool:
        """Remove and verify every artifact created by an initial flow."""
        removed_root = await storage.async_cleanup_project_root()
        if await storage.async_device_identifiers_exists():
            return False
        if session is not None:
            await session.async_clear_credentials()
            if not await session.async_clear_session_file():
                return False
            if await session.async_session_file_exists():
                return False
        return bool(removed_root)

    async def async_fail_closed_reauthentication(
        self, session: SessionTransactionPort
    ) -> bool:
        """Clear active credentials and confirm memory and disk are safe."""
        await session.async_clear_credentials()
        state, session_bytes = await session.async_capture_transaction_state()
        return (
            state.get("username") is None
            and state.get("password") is None
            and state.get("hash_token") is None
            and state.get("refresh_token") is None
            and state.get("is_authenticated") is False
            and session_bytes is None
        )

    async def _restore_entry_and_confirm(
        self,
        *,
        entry: Any,
        previous_data: dict[str, Any],
        update_entry: UpdateEntry,
        reload_entry: ReloadEntry,
        get_entry: GetEntry,
    ) -> None:
        """Restore entry data and verify the persisted/reloaded projection."""
        last_error: Exception | None = None
        for _attempt in range(2):
            try:
                update_entry(entry, data=previous_data)
                if dict(entry.data) != previous_data:
                    raise RuntimeError("entry rollback was not confirmed")
                if await reload_entry(entry.entry_id) is not True:
                    raise RuntimeError("configuration rollback was not confirmed")
                restored_entry = get_entry(entry.entry_id)
                if restored_entry is None or dict(restored_entry.data) != previous_data:
                    raise RuntimeError("reloaded entry rollback was not confirmed")
                return
            except asyncio.CancelledError:
                raise
            except Exception as error:
                last_error = error
        raise RuntimeError("configuration rollback could not be confirmed") from last_error

    async def rollback_reauthentication(
        self,
        *,
        entry: Any,
        previous_data: dict[str, Any],
        session: SessionTransactionPort,
        session_snapshot: dict[str, object] | None,
        session_bytes: bytes | None,
        update_entry: UpdateEntry,
        reload_entry: ReloadEntry,
        get_entry: GetEntry,
    ) -> None:
        """Restore session and entry state, proving both after reload."""
        session_error: BaseException | None = None
        try:
            if session_snapshot is not None:
                await session.async_restore_transaction_state(
                    session_snapshot, session_bytes
                )
                restored_state, restored_bytes = (
                    await session.async_capture_transaction_state()
                )
                if (
                    restored_state != session_snapshot
                    or restored_bytes != session_bytes
                ):
                    raise RuntimeError("session rollback was not confirmed")
            elif not await self.async_fail_closed_reauthentication(session):
                raise RuntimeError("session cleanup was not confirmed")
        except asyncio.CancelledError as cancellation:
            try:
                cleanup_confirmed = await self.async_fail_closed_reauthentication(session)
            except BaseException as cleanup_error:
                raise cancellation from cleanup_error
            if not cleanup_confirmed:
                raise cancellation from RuntimeError("session cleanup could not be confirmed")
            raise
        except Exception as error:
            try:
                cleanup_confirmed = await self.async_fail_closed_reauthentication(session)
            except BaseException as cleanup_error:
                raise RuntimeError("session cleanup could not be confirmed") from cleanup_error
            if not cleanup_confirmed:
                raise RuntimeError("session cleanup could not be confirmed") from error

        await self._restore_entry_and_confirm(
            entry=entry,
            previous_data=previous_data,
            update_entry=update_entry,
            reload_entry=reload_entry,
            get_entry=get_entry,
        )

    async def commit_reauthentication(
        self,
        *,
        entry: Any,
        updated_data: dict[str, Any],
        previous_data: dict[str, Any],
        session: SessionTransactionPort,
        session_snapshot: dict[str, object] | None,
        session_bytes: bytes | None,
        update_entry: UpdateEntry,
        reload_entry: ReloadEntry,
        get_entry: GetEntry,
    ) -> bool:
        """Commit entry data and reload, rolling back every failed attempt."""
        try:
            update_entry(entry, data=updated_data)
            if await reload_entry(entry.entry_id) is not True:
                raise RuntimeError("configuration reload failed")
            reloaded_entry = get_entry(entry.entry_id)
            if reloaded_entry is None or dict(reloaded_entry.data) != updated_data:
                raise RuntimeError("configuration reload was not confirmed")
            return True
        except asyncio.CancelledError as cancellation:
            rollback_task = asyncio.create_task(
                self.rollback_reauthentication(
                    entry=entry,
                    previous_data=previous_data,
                    session=session,
                    session_snapshot=session_snapshot,
                    session_bytes=session_bytes,
                    update_entry=update_entry,
                    reload_entry=reload_entry,
                    get_entry=get_entry,
                )
            )
            try:
                await asyncio.shield(rollback_task)
            except BaseException as rollback_error:
                raise cancellation from rollback_error
            raise
        except Exception:
            await self.rollback_reauthentication(
                entry=entry,
                previous_data=previous_data,
                session=session,
                session_snapshot=session_snapshot,
                session_bytes=session_bytes,
                update_entry=update_entry,
                reload_entry=reload_entry,
                get_entry=get_entry,
            )
            return False

"""Session manager for My Verisure integration."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import tempfile
import threading
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from .file_manager import FileManager
from .utils.jwt_utils import is_jwt_expired
from .log_utils import get_dev_mode

logger = logging.getLogger(__name__)

# Default cooldown after HTTP 403 / rate limit (seconds)
DEFAULT_SERVICE_BLOCKED_COOLDOWN = 600

# Local session age after which we treat the hash as stale (seconds)
TOKEN_MAX_AGE_SECONDS = 3600  # 60 minutes


class SessionManager:
    """Manages authentication session for My Verisure integration."""

    def __init__(
        self,
        session_file: str | os.PathLike[str] | None = None,
        *,
        file_manager: FileManager,
    ) -> None:
        self._is_authenticated = False
        self.current_installation: Any = None
        self.file_manager = file_manager
        expected_session_file = file_manager.get_file_path("session.json")
        if session_file is not None and os.path.abspath(os.fspath(session_file)) != os.path.abspath(os.fspath(expected_session_file)):
            raise ValueError("session_file must be entry-scoped under data/session.json")
        self.session_file = os.fspath(expected_session_file)
        self.username: str | None = None
        self.password: str | None = None
        self.hash_token: str | None = None
        self.refresh_token: str | None = None
        self.session_timestamp: float | None = None
        self._session_disk_hydrated = False
        self._reauthenticator: Callable[[str, str], Awaitable[Any]] | None = None
        # After HTTP 403: pause automatic logins until this monotonic deadline
        self._service_blocked_until: float = 0.0
        self._reauth_failures = 0
        self._last_reauth_attempt_monotonic: float = 0.0
        self._async_persistence_lock = asyncio.Lock()
        self._sync_persistence_lock = threading.RLock()

    def set_authenticator(
        self, authenticator: Callable[[str, str], Awaitable[Any]]
    ) -> None:
        """Set the application-owned authentication boundary for reauth."""
        self._reauthenticator = authenticator

    def set_login_credentials(self, username: str, password: str) -> None:
        """Set non-session login credentials without claiming authentication."""
        if not isinstance(username, str) or not username.strip():
            raise ValueError("username required")
        if not isinstance(password, str) or not password:
            raise ValueError("password required")
        self.username = username
        self.password = password
        self._is_authenticated = False

    @property
    def is_authenticated(self) -> bool:
        """True when username, password and hash_token are present (token may be expired).

        Use :meth:`is_session_valid` when the API requires a non-expired session.
        """
        return bool(self.username and self.password and self.hash_token)

    def _get_session_file_path(self) -> str:
        """Reject unscoped session path resolution."""
        raise RuntimeError("session path must be derived from the injected FileManager")

    def _hydrate_session_from_disk_sync(self) -> None:
        """Load session from file (blocking I/O)."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, encoding="utf-8") as f:
                    session_data = json.load(f)

                self.username = session_data.get("username")
                self.password = session_data.get("password")
                self.hash_token = session_data.get("hash_token")
                self.refresh_token = session_data.get("refresh_token")
                self.session_timestamp = session_data.get("session_timestamp")
                self.current_installation = session_data.get(
                    "current_installation"
                )

                if self._is_token_valid():
                    self._is_authenticated = True
                    logger.info("Valid session loaded from file")
                else:
                    logger.info("Session file present but token expired — re-authentication needed")

        except OSError:
            logger.warning("Could not load session")
        except json.JSONDecodeError:
            logger.warning("Could not parse session file")

    def load_session_sync(self) -> None:
        """Load session from disk synchronously (CLI / tests)."""
        self._hydrate_session_from_disk_sync()
        self._session_disk_hydrated = True

    async def async_load_session_from_disk(self) -> None:
        """Load session from disk without blocking the event loop."""
        await asyncio.to_thread(self._hydrate_session_from_disk_sync)
        self._session_disk_hydrated = True

    def _read_session_file_bytes_sync(self) -> bytes | None:
        """Read the exact prior session file for transactional rollback."""
        try:
            with open(self.session_file, "rb") as file:
                return file.read()
        except FileNotFoundError:
            return None

    def _restore_session_file_sync(self, previous: bytes | None) -> None:
        """Restore a prior session file atomically after a failed write."""
        if previous is None:
            try:
                os.remove(self.session_file)
            except FileNotFoundError:
                return
            return
        parent = os.path.dirname(self.session_file) or "."
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=parent, prefix=".session-rollback-", delete=False
            ) as file:
                temporary_path = file.name
                file.write(previous)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.session_file)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    os.remove(temporary_path)
                except FileNotFoundError:
                    pass


    def _persist_session_to_disk_sync(self) -> None:
        """Write a complete session file and replace the prior file atomically."""
        self.file_manager._ensure_data_directory()
        session_data = {
            "username": self.username,
            "password": self.password,
            "hash_token": self.hash_token,
            "refresh_token": self.refresh_token,
            "session_timestamp": self.session_timestamp,
            "current_installation": self.current_installation,
        }
        parent = os.path.dirname(self.session_file) or "."
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=parent,
                prefix=".session-write-",
                delete=False,
            ) as file:
                temporary_path = file.name
                json.dump(session_data, file)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.session_file)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    os.remove(temporary_path)
                except FileNotFoundError:
                    pass

    async def async_persist_session_to_disk(self) -> None:
        """Persist to disk atomically without blocking or cross-task races."""
        async with self._async_persistence_lock:
            previous = await asyncio.to_thread(self._read_session_file_bytes_sync)
            worker = asyncio.create_task(
                asyncio.to_thread(self._persist_session_to_disk_sync)
            )
            try:
                await asyncio.shield(worker)
                logger.debug("Session saved to file")
            except asyncio.CancelledError:
                try:
                    await asyncio.shield(worker)
                except BaseException:
                    logger.error("Session write failed during cancellation")
                try:
                    await asyncio.to_thread(self._restore_session_file_sync, previous)
                except Exception:
                    logger.error("Session rollback failed during cancellation")
                raise
            except Exception:
                try:
                    await asyncio.to_thread(self._restore_session_file_sync, previous)
                except Exception:
                    logger.error("Session rollback failed")
                logger.error("Could not save session")
                raise

    def _save_session_sync(self) -> None:
        """Save session to file synchronously."""
        with self._sync_persistence_lock:
            previous = self._read_session_file_bytes_sync()
            try:
                self._persist_session_to_disk_sync()
                logger.debug("Session saved to file")
            except Exception:
                try:
                    self._restore_session_file_sync(previous)
                except Exception:
                    logger.error("Session rollback failed")
                logger.error("Could not save session")
                raise

    def _clear_session_file_sync(self) -> bool:
        """Remove session file and report whether absence is confirmed."""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.debug("Session file cleared")
            return not os.path.exists(self.session_file)
        except OSError:
            logger.warning("Could not clear session file")
            return False

    async def async_clear_session_file(self) -> bool:
        """Remove session file without blocking the event loop."""
        return await asyncio.to_thread(self._clear_session_file_sync)

    async def async_session_file_exists(self) -> bool:
        """Check session-file existence without blocking the event loop."""
        return await asyncio.to_thread(os.path.exists, self.session_file)

    def capture_transaction_state(self) -> dict[str, object]:
        """Capture mutable session state for an external transaction."""
        return {
            "username": self.username,
            "password": self.password,
            "hash_token": self.hash_token,
            "refresh_token": self.refresh_token,
            "session_timestamp": self.session_timestamp,
            "current_installation": copy.deepcopy(self.current_installation),
            "is_authenticated": self._is_authenticated,
            "session_disk_hydrated": self._session_disk_hydrated,
        }

    def restore_transaction_state(self, snapshot: dict[str, object]) -> None:
        """Restore mutable session state captured before a transaction."""
        self.username = snapshot.get("username")  # type: ignore[assignment]
        self.password = snapshot.get("password")  # type: ignore[assignment]
        self.hash_token = snapshot.get("hash_token")  # type: ignore[assignment]
        self.refresh_token = snapshot.get("refresh_token")  # type: ignore[assignment]
        self.session_timestamp = snapshot.get("session_timestamp")  # type: ignore[assignment]
        self.current_installation = copy.deepcopy(snapshot.get("current_installation"))
        self._is_authenticated = bool(snapshot.get("is_authenticated"))
        self._session_disk_hydrated = bool(snapshot.get("session_disk_hydrated"))

    async def async_capture_transaction_state(
        self,
    ) -> tuple[dict[str, object], bytes | None]:
        """Capture in-memory state and exact session-file bytes."""
        return self.capture_transaction_state(), await asyncio.to_thread(
            self._read_session_file_bytes_sync
        )

    async def async_restore_transaction_state(
        self, snapshot: dict[str, object], previous_bytes: bytes | None
    ) -> None:
        """Restore memory and the exact prior session file atomically."""
        self.restore_transaction_state(snapshot)
        await asyncio.to_thread(self._restore_session_file_sync, previous_bytes)

    def _load_session(self) -> None:
        """Load session synchronously (tests / legacy); prefer async_load_session_from_disk."""
        self.load_session_sync()

    def _save_session(self) -> None:
        """Deprecated alias for tests: use _save_session_sync."""
        self._save_session_sync()

    def _write_session_file(self, session_data: dict) -> None:
        """Write arbitrary session data atomically for compatibility callers."""
        parent = os.path.dirname(self.session_file) or "."
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=parent,
                prefix=".session-write-",
                delete=False,
            ) as file:
                temporary_path = file.name
                json.dump(session_data, file)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary_path, self.session_file)
            temporary_path = None
        finally:
            if temporary_path is not None:
                try:
                    os.remove(temporary_path)
                except FileNotFoundError:
                    pass

    def _clear_session_file(self) -> None:
        """Clear session file (blocking)."""
        self._clear_session_file_sync()

    def record_service_blocked(self, cooldown_seconds: float = DEFAULT_SERVICE_BLOCKED_COOLDOWN) -> None:
        """Record that the remote service blocked us (e.g. HTTP 403); pause aggressive retries."""
        self._service_blocked_until = max(
            self._service_blocked_until,
            time.monotonic() + cooldown_seconds,
        )
        logger.warning(
            "Service blocked backoff active for %.0f seconds", cooldown_seconds
        )

    def clear_service_blocked(self) -> None:
        """Clear service-blocked backoff after a successful auth."""
        self._service_blocked_until = 0.0
        self._reauth_failures = 0

    def is_service_blocked(self) -> bool:
        """Return True if we should avoid hammering login / reauth."""
        return time.monotonic() < self._service_blocked_until

    def _reauth_backoff_seconds(self) -> float:
        """Exponential backoff for automatic reauthentication (capped)."""
        base = 30.0
        cap = 600.0
        return min(cap, base * (2 ** min(self._reauth_failures, 5)))

    def _is_token_valid(self) -> bool:
        """Check if the stored hash token is still valid."""
        if not self.hash_token:
            logger.debug("No hash token available")
            return False

        if not self.session_timestamp:
            logger.debug("No session timestamp available")
            return False

        current_time = time.time()
        token_age = current_time - self.session_timestamp

        if token_age > TOKEN_MAX_AGE_SECONDS:
            log = logger.warning if get_dev_mode() else logger.debug
            log("Token expired (age: %.1f seconds)", token_age)
            return False

        logger.debug("Token appears valid (age: %.1f seconds)", token_age)
        return True

    async def _try_automatic_reauthentication(self) -> bool:
        """Try automatic reauthentication with a rollback boundary."""
        if self.is_service_blocked():
            return False

        now = time.monotonic()
        wait_for = self._last_reauth_attempt_monotonic + self._reauth_backoff_seconds() - now
        if wait_for > 0:
            await asyncio.sleep(wait_for)

        if self.username is None or self.password is None or self._reauthenticator is None:
            return False

        username = self.username
        password = self.password
        self._last_reauth_attempt_monotonic = time.monotonic()
        snapshot, previous_bytes = await self.async_capture_transaction_state()

        async def rollback() -> None:
            try:
                await self.async_restore_transaction_state(snapshot, previous_bytes)
                restored_state, restored_bytes = await self.async_capture_transaction_state()
                if restored_state != snapshot or restored_bytes != previous_bytes:
                    raise RuntimeError("automatic reauthentication rollback mismatch")
            except asyncio.CancelledError:
                try:
                    self.clear_credentials(persist=False)
                    if not await self.async_clear_session_file():
                        raise RuntimeError("automatic reauthentication cleanup failed")
                    cleared_state, cleared_bytes = await self.async_capture_transaction_state()
                    if (
                        cleared_state.get("username") is not None
                        or cleared_state.get("password") is not None
                        or cleared_state.get("hash_token") is not None
                        or cleared_state.get("refresh_token") is not None
                        or cleared_state.get("is_authenticated") is not False
                        or cleared_bytes is not None
                    ):
                        raise RuntimeError("automatic reauthentication cleanup mismatch")
                except asyncio.CancelledError:
                    raise
                except Exception as cleanup_error:
                    raise RuntimeError(
                        "automatic reauthentication cleanup could not be confirmed"
                    ) from cleanup_error
                raise
            except Exception:
                try:
                    self.clear_credentials(persist=False)
                    if not await self.async_clear_session_file():
                        raise RuntimeError("automatic reauthentication cleanup failed")
                    cleared_state, cleared_bytes = await self.async_capture_transaction_state()
                    if (
                        cleared_state.get("username") is not None
                        or cleared_state.get("password") is not None
                        or cleared_state.get("hash_token") is not None
                        or cleared_state.get("refresh_token") is not None
                        or cleared_state.get("is_authenticated") is not False
                        or cleared_bytes is not None
                    ):
                        raise RuntimeError("automatic reauthentication cleanup mismatch")
                except asyncio.CancelledError:
                    raise
                except Exception as cleanup_error:
                    raise RuntimeError(
                        "automatic reauthentication cleanup could not be confirmed"
                    ) from cleanup_error
                logger.error("Automatic reauthentication rollback replaced by safe cleanup")
                return

        try:
            auth_result = await self._reauthenticator(username, password)
            if not getattr(auth_result, "success", False) or not self.is_session_valid():
                await asyncio.shield(rollback())
                self._reauth_failures += 1
                return False
            self.clear_service_blocked()
            logger.info("Automatic reauthentication successful")
            return True
        except asyncio.CancelledError as cancellation:
            try:
                await asyncio.shield(rollback())
            except BaseException as rollback_error:
                logger.critical("Automatic reauthentication rollback failed")
                raise cancellation from rollback_error
            raise
        except Exception:
            try:
                await asyncio.shield(rollback())
            except asyncio.CancelledError:
                raise
            except Exception as rollback_error:
                logger.critical("Automatic reauthentication rollback failed")
                raise RuntimeError(
                    "Automatic reauthentication rollback could not be confirmed"
                ) from rollback_error
            self._reauth_failures += 1
            logger.warning("Automatic reauthentication failed")
            return False

    def update_credentials(
        self,
        username: str,
        password: str,
        hash_token: str,
        refresh_token: str | None = None,
        *,
        persist: bool = True,
    ) -> None:
        """Update credentials after successful authentication.

        Args:
            persist: If True, write session file synchronously (CLI).
                If False, caller must await async_persist_session_to_disk() (Home Assistant).
        """
        if not isinstance(hash_token, str) or not hash_token.strip():
            raise ValueError("Authenticated session hash required")
        if refresh_token == "":
            raise ValueError("Authenticated refresh token cannot be empty")
        previous = (
            self.username,
            self.password,
            self.hash_token,
            self.refresh_token,
            self.session_timestamp,
            self._is_authenticated,
        )
        self.username = username
        self.password = password
        self.hash_token = hash_token
        self.refresh_token = refresh_token
        self.session_timestamp = time.time()
        self._is_authenticated = True

        try:
            if persist:
                self._save_session_sync()
        except Exception:
            (
                self.username,
                self.password,
                self.hash_token,
                self.refresh_token,
                self.session_timestamp,
                self._is_authenticated,
            ) = previous
            raise
        log = logger.debug if not get_dev_mode() else logger.info
        log("Credentials updated%s", "" if persist else " (persist deferred)")

    async def async_update_credentials(
        self,
        username: str,
        password: str,
        hash_token: str,
        refresh_token: str | None = None,
    ) -> None:
        """Update credentials and persist them without blocking the event loop."""
        snapshot = self.capture_transaction_state()
        previous_bytes = await asyncio.to_thread(self._read_session_file_bytes_sync)
        self.update_credentials(
            username, password, hash_token, refresh_token, persist=False
        )
        try:
            await self.async_persist_session_to_disk()
        except BaseException as original_error:
            rollback_task = asyncio.create_task(
                self.async_restore_transaction_state(snapshot, previous_bytes)
            )
            try:
                await asyncio.shield(rollback_task)
            except asyncio.CancelledError:
                try:
                    await asyncio.shield(rollback_task)
                except BaseException:
                    logger.error("Credential rollback could not be confirmed")
            except BaseException:
                logger.error("Credential rollback could not be confirmed")
            try:
                restored_state, restored_bytes = await self.async_capture_transaction_state()
                if restored_state != snapshot or restored_bytes != previous_bytes:
                    raise RuntimeError("credential rollback state mismatch")
            except BaseException:
                logger.critical("Credential rollback could not be confirmed")
                self.clear_credentials(persist=False)
                cleanup_confirmed = False
                try:
                    cleanup_confirmed = await self.async_clear_session_file()
                except BaseException:
                    logger.critical("Credential fail-closed cleanup failed")
                if not cleanup_confirmed:
                    logger.critical("Credential fail-closed cleanup could not be confirmed")
                    if isinstance(original_error, asyncio.CancelledError):
                        raise original_error
                    raise RuntimeError(
                        "Credential fail-closed cleanup could not be confirmed"
                    ) from original_error
            raise original_error

    def clear_credentials(self, *, persist: bool = True) -> None:
        """Clear all credentials and session data."""
        self._is_authenticated = False
        self.current_installation = None
        self.username = None
        self.password = None
        self.hash_token = None
        self.refresh_token = None
        self.session_timestamp = None

        if persist:
            self._clear_session_file_sync()
        logger.info("Session cleared and cleaned%s", "" if persist else " (file clear deferred)")

    async def async_clear_credentials(self) -> None:
        """Clear credentials and remove session file without blocking the event loop."""
        self.clear_credentials(persist=False)
        if not await self.async_clear_session_file():
            raise RuntimeError("Credential cleanup could not be confirmed")

    def get_current_hash_token(self) -> Optional[str]:
        """Get current hash token."""
        return self.hash_token

    def get_current_session_data(self) -> Optional[Dict[str, Any]]:
        """Get current session data."""
        if self.hash_token and self.username:
            return {
                "user": self.username,
                "login_time": self.session_timestamp,
            }
        return None

    def get_current_cookies(self) -> Optional[Dict[str, str]]:
        """Get persisted cookies when a session actually provides them."""
        return None

    def is_session_valid(self) -> bool:
        """Check if current session is valid."""
        if not self.hash_token or not self.session_timestamp:
            return False

        current_time = time.time()
        session_age = current_time - self.session_timestamp

        if session_age > TOKEN_MAX_AGE_SECONDS:
            logger.info("Session expired by time (age: %.1f seconds)", session_age)
            return False

        try:
            if is_jwt_expired(self.hash_token):
                logger.info("hash_token (JWT) has expired")
                return False
        except Exception:
            logger.error("Unable to validate session token")
            return False

        logger.debug("Session appears valid (age: %.1f seconds)", session_age)
        return True

    def can_attempt_refresh(self) -> bool:
        """True if we should try to refresh the session (have user/pass, not blocked, session invalid).

        Includes the case where hash_token is missing but username/password are set (e.g. from
        config entry) so :meth:`ensure_authenticated` can run a full login.
        """
        has_login_credentials = bool(self.username and self.password)
        return (
            has_login_credentials
            and not self.is_service_blocked()
            and not self.is_session_valid()
        )

    async def ensure_authenticated(self, interactive: bool = True) -> bool:
        """Ensure we have valid authentication, attempting refresh if needed."""
        if not self._session_disk_hydrated:
            await self.async_load_session_from_disk()

        if self.is_session_valid():
            logger.debug("Valid session found, no authentication needed")
            logger.debug(
                "AUTH_FLOW[ensure_authenticated]: result=%s, valid=%s, blocked=%s",
                "success",
                self.is_session_valid(),
                self.is_service_blocked(),
            )
            return True

        if self.is_service_blocked():
            logger.warning(
                "Service blocked - cannot authenticate, caller should use cached data"
            )
            logger.debug(
                "AUTH_FLOW[ensure_authenticated]: result=%s, valid=%s, blocked=%s",
                "failed",
                self.is_session_valid(),
                self.is_service_blocked(),
            )
            return False

        logger.info("Session expired — clearing detailed installation cache")
        await self.file_manager.async_delete_files_by_prefix("detailed_installation_")

        if not self.username or not self.password:
            if interactive:
                self.username, self.password = await asyncio.to_thread(
                    self._get_user_credentials
                )
                logger.debug(
                    "AUTH_FLOW[ensure_authenticated]: result=%s, valid=%s, blocked=%s",
                    "success",
                    self.is_session_valid(),
                    self.is_service_blocked(),
                )
                return True
            logger.error("No credentials available and non-interactive mode")
            logger.debug(
                "AUTH_FLOW[ensure_authenticated]: result=%s, valid=%s, blocked=%s",
                "failed",
                self.is_session_valid(),
                self.is_service_blocked(),
            )
            return False

        logger.info(
            "Session expired — attempting automatic reauthentication"
        )
        reauth_ok = await self._try_automatic_reauthentication()
        logger.debug(
            "AUTH_FLOW[ensure_authenticated]: result=%s, valid=%s, blocked=%s",
            "success" if reauth_ok else "failed",
            self.is_session_valid(),
            self.is_service_blocked(),
        )
        return reauth_ok

    def _get_user_credentials(self) -> tuple[str, str]:
        """Get user credentials interactively."""
        print("\n============================================================")
        print("🚀 MY VERISURE - AUTENTICACIÓN INTERACTIVA")
        print("============================================================")
        print("👤 Ingresa tus credenciales de My Verisure:")
        print()

        try:
            username = input("📋 User ID (DNI/NIE): ").strip()
            password = input("🔐 Contraseña: ").strip()
            return username, password
        except EOFError as e:
            raise RuntimeError(
                "No se pueden obtener credenciales en modo no interactivo"
            ) from e

    async def logout(self) -> None:
        """Logout and clear session."""
        logger.info("Logging out and clearing session")
        await self.async_clear_credentials()
        logger.info("Logout completed")

    async def cleanup(self) -> None:
        """Clean up resources."""
        await self.async_clear_credentials()

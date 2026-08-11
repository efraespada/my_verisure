"""Session manager for My Verisure integration."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Awaitable, Callable, Dict, Optional

from .file_manager import FileManager, get_file_manager
from .utils.jwt_utils import is_jwt_expired
from .log_utils import get_dev_mode

logger = logging.getLogger(__name__)

# Global singleton instance
_session_manager_instance: Optional["SessionManager"] = None

# Default cooldown after HTTP 403 / rate limit (seconds)
DEFAULT_SERVICE_BLOCKED_COOLDOWN = 600

# Local session age after which we treat the hash as stale (seconds)
TOKEN_MAX_AGE_SECONDS = 3600  # 60 minutes


class SessionManager:
    """Manages authentication session for My Verisure integration."""

    def __init__(
        self,
        session_file: str | os.PathLike[str] | None = None,
        file_manager: FileManager | None = None,
    ) -> None:
        self._is_authenticated = False
        self.current_installation = None
        self.session_file = (
            os.fspath(session_file)
            if session_file is not None
            else self._get_session_file_path()
        )
        self.file_manager = file_manager or get_file_manager()
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

    def set_authenticator(
        self, authenticator: Callable[[str, str], Awaitable[Any]]
    ) -> None:
        """Set the application-owned authentication boundary for reauth."""
        self._reauthenticator = authenticator

    @property
    def is_authenticated(self) -> bool:
        """True when username, password and hash_token are present (token may be expired).

        Use :meth:`is_session_valid` when the API requires a non-expired session.
        """
        return bool(self.username and self.password and self.hash_token)

    def _get_session_file_path(self) -> str:
        """Get the session file path."""
        home_dir = os.path.expanduser("~")
        session_dir = os.path.join(home_dir, ".my_verisure")
        os.makedirs(session_dir, exist_ok=True)
        return os.path.join(session_dir, "session.json")

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

        except OSError as e:
            logger.warning("Could not load session: %s", e)
        except json.JSONDecodeError as e:
            logger.warning("Could not parse session file: %s", e)

    def load_session_sync(self) -> None:
        """Load session from disk synchronously (CLI / tests)."""
        self._hydrate_session_from_disk_sync()
        self._session_disk_hydrated = True

    async def async_load_session_from_disk(self) -> None:
        """Load session from disk without blocking the event loop."""
        await asyncio.to_thread(self._hydrate_session_from_disk_sync)
        self._session_disk_hydrated = True

    def _persist_session_to_disk_sync(self) -> None:
        """Write session to file (blocking I/O)."""
        session_data = {
            "username": self.username,
            "password": self.password,
            "hash_token": self.hash_token,
            "refresh_token": self.refresh_token,
            "session_timestamp": self.session_timestamp,
            "current_installation": self.current_installation,
        }
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f)

    async def async_persist_session_to_disk(self) -> None:
        """Persist session to disk without blocking the event loop."""
        try:
            await asyncio.to_thread(self._persist_session_to_disk_sync)
            logger.debug("Session saved to file")
        except OSError as e:
            logger.error("Could not save session: %s", e)

    def _save_session_sync(self) -> None:
        """Save session to file synchronously."""
        try:
            self._persist_session_to_disk_sync()
            logger.debug("Session saved to file")
        except OSError as e:
            logger.error("Could not save session: %s", e)

    def _clear_session_file_sync(self) -> None:
        """Remove session file (blocking I/O)."""
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                logger.debug("Session file cleared")
        except OSError as e:
            logger.warning("Could not clear session file: %s", e)

    async def async_clear_session_file(self) -> None:
        """Remove session file without blocking the event loop."""
        await asyncio.to_thread(self._clear_session_file_sync)

    def _load_session(self) -> None:
        """Load session synchronously (tests / legacy); prefer async_load_session_from_disk."""
        self.load_session_sync()

    def _save_session(self) -> None:
        """Deprecated alias for tests: use _save_session_sync."""
        self._save_session_sync()

    def _write_session_file(self, session_data: dict) -> None:
        """Write session data to file (blocking operation)."""
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f)

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
        """Try to reauthenticate automatically using stored credentials."""
        if self.is_service_blocked():
            log = logger.warning if get_dev_mode() else logger.debug
            log(
                "Skipping automatic reauthentication while service-blocked backoff is active"
            )
            return False

        now = time.monotonic()
        wait_for = self._last_reauth_attempt_monotonic + self._reauth_backoff_seconds() - now
        if wait_for > 0:
            log = logger.warning if get_dev_mode() else logger.debug
            log(
                "Reauthentication backoff: waiting %.1f seconds before retry",
                wait_for,
            )
            await asyncio.sleep(wait_for)

        try:
            logger.debug(
                "AUTH_FLOW[reauth_attempt]: attempt_count=%s, backoff_seconds=%.1f, last_attempt_age=%.1f",
                self._reauth_failures,
                self._reauth_backoff_seconds(),
                time.monotonic() - self._last_reauth_attempt_monotonic
                if self._last_reauth_attempt_monotonic > 0
                else 0.0,
            )
            logger.info(
                "Attempting automatic reauthentication with stored credentials..."
            )

            if self.username is None or self.password is None:
                logger.warning("Cannot reauthenticate without stored credentials")
                return False

            username = self.username
            password = self.password
            self._last_reauth_attempt_monotonic = time.monotonic()
            if self._reauthenticator is None:
                logger.warning("Cannot reauthenticate without an injected authenticator")
                return False

            auth_result = await self._reauthenticator(username, password)

            if auth_result.success:
                self.update_credentials(
                    username,
                    password,
                    auth_result.hash,
                    auth_result.refresh_token,
                    persist=False,
                )
                await self.async_persist_session_to_disk()
                self.clear_service_blocked()
                logger.info("Automatic reauthentication successful")
                return True

            self._reauth_failures += 1
            logger.warning(
                "Automatic reauthentication failed: %s", auth_result.message
            )
            return False

        except Exception as e:
            self._reauth_failures += 1
            logger.warning("Automatic reauthentication failed: %s", e)
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
        self.username = username
        self.password = password
        self.hash_token = hash_token
        self.refresh_token = refresh_token
        self.session_timestamp = time.time()
        self._is_authenticated = True

        if persist:
            self._save_session_sync()
        log = logger.debug if not get_dev_mode() else logger.info
        log("Credentials updated%s", "" if persist else " (persist deferred)")

    async def async_update_credentials(
        self,
        username: str,
        password: str,
        hash_token: str,
        refresh_token: str | None = None,
    ) -> None:
        """Update credentials and persist to disk without blocking the event loop."""
        self.update_credentials(
            username, password, hash_token, refresh_token, persist=False
        )
        await self.async_persist_session_to_disk()

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
        await self.async_clear_session_file()

    def get_current_hash_token(self) -> Optional[str]:
        """Get current hash token."""
        return self.hash_token

    def get_current_session_data(self) -> Optional[Dict[str, Any]]:
        """Get current session data."""
        if self.hash_token and self.username:
            return {
                "user": self.username,
                "lang": "ES",
                "legals": True,
                "changePassword": False,
                "needDeviceAuthorization": None,
                "login_time": self.session_timestamp or time.time(),
            }
        return None

    def get_current_cookies(self) -> Optional[Dict[str, str]]:
        """Get current cookies."""
        return {}

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
        except Exception as e:
            log = logger.warning if get_dev_mode() else logger.debug
            log("Error checking JWT expiration: %s", e)

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
                self.username, self.password = self._get_user_credentials()
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


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance

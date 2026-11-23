"""Entry-owned FCM receiver with bounded recovery and private persistence.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import base64
from collections.abc import Callable
import copy
import json
import logging
from typing import Any, Protocol, runtime_checkable

import aiohttp
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, load_der_private_key,
)
from firebase_messaging import FcmPushClient, FcmPushClientConfig, FcmRegisterConfig
from firebase_messaging.proto.mcs_pb2 import LoginResponse

from ..file_manager import FileManager
from .public_push_config import async_resolve_public_api_key
from .push_config import PROJECT_ID, APP_ID, MESSAGING_SENDER_ID
from .push_decoder import b64, decode
from .push_storage import PrivatePushStore

_LOGGER = logging.getLogger(__name__)
MAX_MCS_FRAME_BYTES = 256 * 1024
MAX_REPLAY_STATE_BYTES = 128 * 1024


class NotificationSink(Protocol):
    """Entry-owned notification consumer, independent of photo correlation."""

    connected: bool

    @property
    def recent_ids(self) -> list[str]: ...

    def restore_ids(self, values: list[str]) -> None: ...

    def receive(self, payload: dict[str, Any], persistent_id: str) -> None: ...

    def close(self) -> None: ...


@runtime_checkable
class ReplayStateSink(Protocol):
    """Optional private, versioned replay state owned by the application."""

    def export_replay(self) -> dict[str, Any]: ...

    def restore_replay(self, state: dict[str, Any]) -> None: ...


def _checked_replay(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Invalid notification replay state")
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_REPLAY_STATE_BYTES:
            raise ValueError("Notification replay state exceeds its limit")
        return copy.deepcopy(value)
    except (TypeError, ValueError, RecursionError):
        raise ValueError("Invalid notification replay state") from None


class VerisureFcmClient(FcmPushClient):
    """Adapter for the observed combined Crypto-Key header in SDK 0.4.5."""

    registration_invalid = False
    invalid_messages = 0

    async def _read_varint32(self) -> int:
        """Bound SDK frame allocation before it reads or parses the body."""
        if self.reader is None:
            raise ValueError("MCS frame stream is unavailable")
        size = 0
        for index in range(5):
            byte = (await self.reader.readexactly(1))[0]
            if index == 4 and byte & 0xF0:
                raise ValueError("Invalid MCS frame length")
            size |= (byte & 0x7F) << (7 * index)
            if size > MAX_MCS_FRAME_BYTES:
                raise ValueError("MCS frame exceeds the size limit")
            if not byte & 0x80:
                return size
        raise ValueError("Invalid MCS frame length")

    async def _handle_message(self, message: Any) -> None:
        if isinstance(message, LoginResponse) and str(message.error):
            self.registration_invalid = True
        await super()._handle_message(message)

    def _handle_data_message(self, message: Any) -> None:
        try:
            if hasattr(self, "persistent_ids"):
                self.persistent_ids[:] = self.persistent_ids[-127:]
            if self.credentials is None:
                self.invalid_messages += 1
                return
            if len(message.raw_data) > 65536 or len(message.app_data) > 20:
                self.invalid_messages += 1
                return
            if any(len(item.key) > 256 or len(item.value) > 4096 for item in message.app_data):
                self.invalid_messages += 1
                return
            fields = [{"key": item.key, "value": item.value} for item in message.app_data]
            record = {"envelope": {
                "raw_data": base64.b64encode(message.raw_data).decode("ascii"),
                "app_data": fields,
            }}
            payload = decode(record, self.credentials)
            if not isinstance(payload, dict) or str(payload.get("from")) != MESSAGING_SENDER_ID:
                self.invalid_messages += 1
                return
            self.callback(payload, message.persistent_id, self.callback_context)
        except Exception:
            self.invalid_messages += 1
            # Neither SDK exception strings nor encrypted/provider payloads belong in logs.
            _LOGGER.debug("Ignored an invalid push message")


class PushReceiver:
    """Own registration, listener tasks and state for one HA config entry."""

    def __init__(
        self, files: FileManager, notifications: NotificationSink,
        http_session: aiohttp.ClientSession | None = None,
        client_factory: Any = VerisureFcmClient,
        on_token_changed: Callable[[str], None] | None = None,
    ) -> None:
        self.notifications = notifications
        self._store = PrivatePushStore(files)
        self._http_session = http_session
        self._factory = client_factory
        self._on_token_changed = on_token_changed
        self._credentials: dict[str, Any] | None = None
        self._token: str | None = None
        self._public_api_key = ""
        self._client: Any = None
        self._runner: asyncio.Task | None = None
        self._writer: asyncio.Task | None = None
        self._dirty = False
        self._closing = False
        self._prepare_lock = asyncio.Lock()
        self._ready = asyncio.Event()
        self._refresh_registration = False
        self.received = 0
        self.reconnects = 0
        self.persistence_failures = 0
        self.invalid_cached_credentials = 0

    @property
    def connected(self) -> bool:
        return bool(self._client is not None and self._client.is_started())

    @property
    def token(self) -> str | None:
        return self._token

    def diagnostics(self) -> dict[str, Any]:
        return {"connected": self.connected, "received": self.received,
                "reconnects": self.reconnects, "persistence_failures": self.persistence_failures,
                "invalid_cached_credentials": self.invalid_cached_credentials,
                "invalid_messages": getattr(self._client, "invalid_messages", 0)}

    def _save_later(self) -> None:
        self._dirty = True
        if self._writer is None or self._writer.done():
            self._writer = asyncio.create_task(self._flush())

    def request_state_save(self) -> None:
        """Persist new local verified replay metadata while credentials are owned."""
        if not self._closing and self._credentials is not None:
            self._save_later()

    def _resume_ids(self, values: object = None) -> list[str]:
        candidates = self.notifications.recent_ids if values is None else values
        if not isinstance(candidates, list):
            return []
        return [value for value in candidates if isinstance(value, str) and 0 < len(value) <= 512][-128:]

    async def _flush(self) -> None:
        try:
            while self._dirty:
                self._dirty = False
                state: dict[str, Any] = {
                    "credentials": copy.deepcopy(self._credentials),
                    "persistent_ids": self._resume_ids(),
                }
                if isinstance(self.notifications, ReplayStateSink):
                    state["notification_replay"] = _checked_replay(self.notifications.export_replay())
                await self._store.save("push_credentials.json", state)
        except asyncio.CancelledError:
            # The store drains its thread before cancellation escapes. Retrying
            # preparation must still conservatively persist the current snapshot.
            self._dirty = True
            raise
        except Exception:
            self._dirty = True
            self.persistence_failures += 1
            _LOGGER.warning("Push state could not be persisted; polling remains available")

    def _credentials_updated(self, value: dict[str, Any]) -> None:
        if self._closing:
            return
        token = value["fcm"]["registration"]["token"]
        if not isinstance(token, str) or not 10 <= len(token) <= 4096:
            raise ValueError("Invalid receiver registration token")
        previous = self._token
        self._credentials = copy.deepcopy(value)
        self._token = token
        self._save_later()
        if self._token != previous and self._on_token_changed is not None:
            try:
                self._on_token_changed(token)
            except Exception:
                _LOGGER.warning("Push token-change callback failed; reconciliation remains pending")

    def _received(self, payload: dict[str, Any], persistent_id: str, context: Any) -> None:
        if self._closing:
            return
        self.received += 1
        self.notifications.receive(payload, persistent_id)
        self._save_later()

    def _new_client(self) -> Any:
        return self._factory(
            self._received,
            FcmRegisterConfig(PROJECT_ID, APP_ID, self._public_api_key, MESSAGING_SENDER_ID,
                              bundle_id="home-assistant-my-verisure"),
            self._credentials, self._credentials_updated,
            received_persistent_ids=self._resume_ids(),
            http_client_session=self._http_session,
            config=FcmPushClientConfig(
                connection_retry_count=3, start_seconds_before_retry_connect=5,
                reset_interval=30, client_heartbeat_interval=60,
                server_heartbeat_interval=60, log_warn_limit=1,
            ),
        )

    def _cached_token(self) -> str | None:
        """Reuse durable credentials; MCS validates them without new HTTP registration."""
        try:
            value = self._credentials
            if not isinstance(value, dict) or value["config"]["project_id"] != PROJECT_ID:
                return None
            keys, gcm = value["keys"], value["gcm"]
            if not all(
                isinstance(keys[key], str) and 0 < len(keys[key]) <= 4096
                for key in ("private", "public", "secret")
            ):
                return None
            private = load_der_private_key(b64(keys["private"]), password=None)
            if (
                not isinstance(private, ec.EllipticCurvePrivateKey)
                or not isinstance(private.curve, ec.SECP256R1)
            ):
                return None
            public = private.public_key().public_bytes(
                Encoding.X962, PublicFormat.UncompressedPoint,
            )
            if b64(keys["public"]) != public or len(b64(keys["secret"])) != 16:
                return None
            if not all(
                str(gcm[key]).isdigit() and int(gcm[key]) > 0
                for key in ("android_id", "security_token")
            ):
                return None
            if not isinstance(gcm["app_id"], str) or not gcm["app_id"]:
                return None
            token = value["fcm"]["registration"]["token"]
            return token if isinstance(token, str) and 10 <= len(token) <= 4096 else None
        except (KeyError, TypeError, ValueError, UnsupportedAlgorithm):
            return None

    async def async_prepare(self) -> str:
        async with self._prepare_lock:
            if self._token:
                if self._dirty:
                    self._save_later()
                if self._writer:
                    await self._writer
                if self._dirty:
                    raise OSError("Push state is not persisted")
                return self._token
            stored = await self._store.load("push_credentials.json")
            value = stored.get("credentials")
            self._credentials = value if isinstance(value, dict) else None
            self.notifications.restore_ids(self._resume_ids(stored.get("persistent_ids", [])))
            replay = stored.get("notification_replay")
            if replay is not None and isinstance(self.notifications, ReplayStateSink):
                try:
                    self.notifications.restore_replay(_checked_replay(replay))
                except Exception:
                    _LOGGER.warning("Stored notification replay state is invalid; keeping transport credentials")
            cached_token = self._cached_token()
            if cached_token:
                self._client = self._new_client()
                self._token = cached_token
                return cached_token
            if self._credentials is not None:
                self.invalid_cached_credentials += 1
                _LOGGER.warning("Stored push credentials are invalid; registering a new receiver")
            # A successful GCM check-in would otherwise return these same broken
            # crypto keys without rebuilding the receiver registration.
            self._credentials = None
            self._public_api_key = await async_resolve_public_api_key(self._http_session)
            self._client = self._new_client()
            try:
                async with asyncio.timeout(45):
                    self._token = await self._client.checkin_or_register()
                self._credentials = copy.deepcopy(self._client.credentials)
                self._save_later()
                if self._writer:
                    await self._writer
                if self._dirty or not self._token:
                    raise OSError("Push registration is not persisted")
                return self._token
            finally:
                register = getattr(self._client, "register", None)
                if register is not None:
                    await register.close()

    async def async_start(self) -> bool:
        if self._runner is None:
            self._runner = asyncio.create_task(self._run())
        try:
            await asyncio.wait_for(self._ready.wait(), 20)
        except TimeoutError:
            pass
        return self.connected

    async def _run(self) -> None:
        delay = 30
        try:
            while not self._closing:
                client = self._client
                try:
                    if client is None:
                        if self._refresh_registration:
                            self._public_api_key = await async_resolve_public_api_key(self._http_session)
                        client = self._new_client()
                        self._client = client
                        if self._refresh_registration:
                            async with asyncio.timeout(45):
                                await client.checkin_or_register()
                            self._refresh_registration = False
                    await client.start()
                    async with asyncio.timeout(20):
                        while not client.is_started():
                            await asyncio.sleep(0.1)
                    self.notifications.connected = True
                    self._ready.set()
                    _LOGGER.info("Push receiver connected")
                    delay = 30
                    while not self._closing and all(not task.done() for task in client.tasks):
                        await asyncio.sleep(5)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    _LOGGER.warning("Push receiver unavailable; using polling fallback")
                    self._ready.set()
                finally:
                    self.notifications.connected = False
                    if client is not None:
                        if getattr(client, "registration_invalid", False):
                            self._refresh_registration = True
                        if getattr(client, "stopping_lock", None) is not None:
                            await client.stop()
                        # SDK stop() can return early after a failed connection.
                        # Always own and drain its tasks, including that case.
                        tasks = getattr(client, "tasks", [])
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        register = getattr(client, "register", None)
                        if register is not None:
                            await register.close()
                    self._client = None
                if not self._closing:
                    self.reconnects += 1
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 900)
        finally:
            self.notifications.connected = False

    async def async_stop(self) -> None:
        self._closing = True
        self.notifications.close()
        if self._runner is not None:
            self._runner.cancel()
            await asyncio.gather(self._runner, return_exceptions=True)
            self._runner = None
        if self._writer is not None:
            await asyncio.gather(self._writer, return_exceptions=True)

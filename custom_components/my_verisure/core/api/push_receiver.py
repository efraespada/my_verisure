"""Entry-owned FCM receiver with bounded recovery and private persistence.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import base64
import copy
import logging
from typing import Any

import aiohttp
from firebase_messaging import FcmPushClient, FcmPushClientConfig, FcmRegisterConfig
from firebase_messaging.proto.mcs_pb2 import LoginResponse

from ..application.photo_notifications import PhotoNotifications
from ..file_manager import FileManager
from .public_push_config import async_resolve_public_api_key
from .push_config import PROJECT_ID, APP_ID, MESSAGING_SENDER_ID
from .push_decoder import decode
from .push_storage import PrivatePushStore

_LOGGER = logging.getLogger(__name__)


class VerisureFcmClient(FcmPushClient):
    """Adapter for the observed combined Crypto-Key header in SDK 0.4.5."""

    registration_invalid = False

    async def _handle_message(self, message: Any) -> None:
        if isinstance(message, LoginResponse) and str(message.error):
            self.registration_invalid = True
        await super()._handle_message(message)

    def _handle_data_message(self, message: Any) -> None:
        try:
            if hasattr(self, "persistent_ids"):
                self.persistent_ids[:] = self.persistent_ids[-127:]
            if self.credentials is None:
                return
            if len(message.raw_data) > 65536 or len(message.app_data) > 20:
                return
            if any(len(item.key) > 256 or len(item.value) > 4096 for item in message.app_data):
                return
            fields = [{"key": item.key, "value": item.value} for item in message.app_data]
            record = {"envelope": {
                "raw_data": base64.b64encode(message.raw_data).decode("ascii"),
                "app_data": fields,
            }}
            payload = decode(record, self.credentials)
            if not isinstance(payload, dict) or str(payload.get("from")) != MESSAGING_SENDER_ID:
                return
            self.callback(payload, message.persistent_id, self.callback_context)
        except Exception:
            # Neither SDK exception strings nor encrypted/provider payloads belong in logs.
            _LOGGER.debug("Ignored an invalid push message")


class PushReceiver:
    """Own registration, listener tasks and state for one HA config entry."""

    def __init__(
        self, files: FileManager, notifications: PhotoNotifications,
        http_session: aiohttp.ClientSession | None = None,
        client_factory: Any = VerisureFcmClient,
    ) -> None:
        self.notifications = notifications
        self._store = PrivatePushStore(files)
        self._http_session = http_session
        self._factory = client_factory
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

    @property
    def connected(self) -> bool:
        return bool(self._client is not None and self._client.is_started())

    @property
    def token(self) -> str | None:
        return self._token

    def diagnostics(self) -> dict[str, Any]:
        return {"connected": self.connected, "received": self.received,
                "reconnects": self.reconnects}

    def _save_later(self) -> None:
        self._dirty = True
        if self._writer is None or self._writer.done():
            self._writer = asyncio.create_task(self._flush())

    async def _flush(self) -> None:
        try:
            while self._dirty:
                self._dirty = False
                await self._store.save("push_credentials.json", {
                    "credentials": copy.deepcopy(self._credentials),
                    "persistent_ids": self.notifications.recent_ids,
                })
        except Exception:
            self._dirty = True
            _LOGGER.warning("Push state could not be persisted; polling remains available")

    def _credentials_updated(self, value: dict[str, Any]) -> None:
        self._credentials = copy.deepcopy(value)
        self._token = value["fcm"]["registration"]["token"]
        self._save_later()

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
            received_persistent_ids=self.notifications.recent_ids,
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
                isinstance(keys[key], str) and keys[key]
                for key in ("private", "public", "secret")
            ):
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
        except (KeyError, TypeError, ValueError):
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
            ids = stored.get("persistent_ids", [])
            self.notifications.restore_ids(ids if isinstance(ids, list) else [])
            cached_token = self._cached_token()
            if cached_token:
                self._client = self._new_client()
                self._token = cached_token
                return cached_token
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
            await self._writer

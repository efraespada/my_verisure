"""Entry-scoped push activation and native profile reconciliation.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
import logging
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .core.api.device_manager import DeviceManager
from .core.api.push_receiver import PushReceiver
from .core.application.photo_notifications import PhotoNotifications
from .core.dependency_injection.composition_root import CompositionRoot
from .core.file_manager import FileManager
from .core.session_manager import SessionManager
from .core.utils.jwt_utils import get_jwt_payload

_LOGGER = logging.getLogger(__name__)


async def async_reconcile_profile(
    device: DeviceManager, session: SessionManager,
) -> None:
    """Load the persisted profile before considering a cached access session."""
    await device.async_ensure_device_identifiers()
    payload = get_jwt_payload(session.hash_token or "") or {}
    callby = payload.get("callBy", payload.get("callby"))
    if callby and callby != device.profile_context.current.callby:
        session.hash_token = None
        session.refresh_token = None


class HomeAssistantPush:
    """Prepare once, retain the token and stop all tasks on entry unload."""

    def __init__(self, hass: HomeAssistant, root: CompositionRoot) -> None:
        self._hass = hass
        self._root = root
        self._lock = asyncio.Lock()
        self._retry_at = 0.0
        self.receiver: PushReceiver | None = None

    async def async_prepare(self) -> None:
        """Register before login; a failed receiver leaves polling available."""
        async with self._lock:
            if time.monotonic() < self._retry_at:
                return
            if self.receiver is None:
                self.receiver = PushReceiver(
                    self._root.get(FileManager),
                    self._root.get(PhotoNotifications),
                    http_session=async_get_clientsession(self._hass),
                )
            try:
                token = await self.receiver.async_prepare()
                device = self._root.get(DeviceManager)
                previous = device.profile_context.current.callby
                changed = await device.async_set_push_token(token)
                if changed:
                    session = self._root.get(SessionManager)
                    session.hash_token = None
                    if previous != "OWA_10":
                        session.refresh_token = None
                    _LOGGER.info("Native push profile prepared for authentication")
                await self.receiver.async_start()
            except asyncio.CancelledError:
                raise
            except Exception:
                self._retry_at = time.monotonic() + 900
                _LOGGER.warning("Push setup unavailable; polling remains enabled")

    async def async_stop(self) -> None:
        """Cancel listener and pending push waits before unloading the entry."""
        if self.receiver is not None:
            await self.receiver.async_stop()

    def diagnostics(self) -> dict:
        """Return counters and connection state, never credentials or tokens."""
        return self.receiver.diagnostics() if self.receiver else {"connected": False}

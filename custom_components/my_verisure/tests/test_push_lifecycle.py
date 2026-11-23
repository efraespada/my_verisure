"""Exercise entry profile transitions and optional push lifecycle in HA.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

from unittest.mock import AsyncMock, Mock

import jwt
import pytest

from custom_components.my_verisure import push
from custom_components.my_verisure.core.api.device_manager import DeviceManager
from custom_components.my_verisure.core.dependency_injection.composition_root import build_my_verisure_composition_root
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_activation_restart_rotation_and_close(hass, tmp_path, monkeypatch):
    root = build_my_verisure_composition_root(project_root=tmp_path, push_enabled=True)
    device = root.get(DeviceManager)
    session = root.get(SessionManager)
    await device.async_ensure_device_identifiers()
    before = device.get_device_identifiers()["uuid"]
    session.hash_token, session.refresh_token = "old-ios", "old-refresh"
    receiver = AsyncMock()
    receiver.request_state_save = Mock()
    receiver.async_prepare.return_value = "synthetic-fcm-token"
    monkeypatch.setattr(push, "PushReceiver", lambda *args, **kwargs: receiver)
    adapter = push.HomeAssistantPush(hass, root)
    await adapter.async_prepare()
    assert session.hash_token is None and session.refresh_token is None
    assert device.get_device_identifiers()["uuid"] == before
    session.hash_token, session.refresh_token = "android", "android-refresh"
    await adapter.async_finish_auth(True)
    await adapter.async_prepare()
    assert session.hash_token == "android"
    await adapter.async_finish_auth(True)
    receiver.async_prepare.return_value = "synthetic-rotated-token"
    await adapter.async_prepare()
    assert session.hash_token is None and session.refresh_token == "android-refresh"
    session.hash_token = "rotated-android"
    await adapter.async_finish_auth(True)
    await adapter.async_stop()
    receiver.async_stop.assert_awaited_once()
    restored = build_my_verisure_composition_root(project_root=tmp_path)
    reloaded = restored.get(SessionManager)
    reloaded.hash_token = jwt.encode({"callBy": "OWI_10"}, "synthetic-session-signing-key-for-test-only", algorithm="HS256")
    reloaded.refresh_token = "old-ios-refresh"
    await push.async_reconcile_profile(restored.get(DeviceManager), reloaded)
    assert restored.get(DeviceManager).profile_context.current.callby == "OWA_10"
    assert reloaded.hash_token is None and reloaded.refresh_token is None


@pytest.mark.homeassistant
@pytest.mark.asyncio
async def test_failed_fcm_registration_keeps_session_and_backs_off(hass, tmp_path, monkeypatch):
    root = build_my_verisure_composition_root(project_root=tmp_path, push_enabled=True)
    session = root.get(SessionManager)
    session.hash_token = "existing"
    receiver = AsyncMock()
    receiver.request_state_save = Mock()
    receiver.async_prepare.side_effect = OSError("synthetic")
    monkeypatch.setattr(push, "PushReceiver", lambda *args, **kwargs: receiver)
    adapter = push.HomeAssistantPush(hass, root)
    await adapter.async_prepare()
    await adapter.async_prepare()
    receiver.async_prepare.assert_awaited_once()
    assert session.hash_token == "existing"
    receiver.async_start.assert_not_awaited()
    await adapter.async_stop()

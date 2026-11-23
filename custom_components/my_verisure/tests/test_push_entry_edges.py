"""Entry lifecycle edges retain transaction and transport ownership.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from unittest.mock import Mock

import pytest

from custom_components.my_verisure import push
from .test_push_auth_transaction import binding as _binding_fixture

binding = _binding_fixture

pytestmark = [pytest.mark.homeassistant, pytest.mark.asyncio]


async def test_disabled_and_closed_receiver_do_not_start_network(hass):
    root = Mock()
    adapter = push.HomeAssistantPush(hass, root, enabled=False)
    await adapter.async_prepare()
    root.get.assert_not_called()
    assert adapter.diagnostics()["binding_state"] == "disabled"
    await adapter.async_stop()
    adapter._token_changed("synthetic-after-close")
    await adapter.async_prepare()
    assert adapter.receiver is None and adapter._latest_token is None


async def test_repeated_prepare_before_auth_keeps_same_transaction(binding):
    await binding.adapter.async_prepare()
    stage = binding.adapter._stage
    await binding.adapter.async_prepare()
    assert binding.adapter._stage is stage
    await binding.adapter.async_finish_auth(False)


async def test_cancelled_prepare_rolls_back_and_propagates(binding):
    binding.receiver.async_start.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await binding.adapter.async_prepare()
    assert binding.adapter._stage is None
    assert binding.session.hash_token == "synthetic-ios-access"


async def test_closing_during_receiver_registration_never_stages_address(binding):
    entered, release = asyncio.Event(), asyncio.Event()

    async def registration():
        entered.set()
        await release.wait()
        return "synthetic-fcm-address"

    binding.receiver.async_prepare.side_effect = registration
    prepare = asyncio.create_task(binding.adapter.async_prepare())
    await entered.wait()
    close = asyncio.create_task(binding.adapter.async_stop())
    await asyncio.sleep(0)
    release.set()
    await asyncio.gather(prepare, close)
    assert binding.adapter._stage is None
    binding.receiver.async_start.assert_not_awaited()
    binding.receiver.async_stop.assert_awaited_once()


async def test_waiting_prepare_is_rejected_when_unload_closes_admission(binding):
    await binding.adapter._lock.acquire()
    prepare = asyncio.create_task(binding.adapter.async_prepare())
    await asyncio.sleep(0)
    close = asyncio.create_task(binding.adapter.async_stop())
    await asyncio.sleep(0)
    binding.adapter._lock.release()
    await asyncio.gather(prepare, close)
    binding.receiver.async_prepare.assert_not_awaited()


async def test_missing_jwt_profile_does_not_invalidate_existing_credential(binding):
    binding.session.hash_token = "synthetic-not-a-jwt"
    await push.async_reconcile_profile(binding.device, binding.session)
    assert binding.session.hash_token == "synthetic-not-a-jwt"

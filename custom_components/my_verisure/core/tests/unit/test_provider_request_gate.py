"""Cross-client provider cooldown, concurrency and cancellation regressions.

Generated with ha-integration@aurora-smart-home v1.1.0
https://github.com/tonylofgren/aurora-smart-home
"""

import asyncio
from datetime import datetime, timezone
from email.utils import format_datetime
import gc
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import weakref

import pytest

from custom_components.my_verisure.core.api import base_client
from custom_components.my_verisure.core.api.base_client import BaseClient
from custom_components.my_verisure.core.api.provider_request_gate import (
    ProviderRequestGate,
    get_provider_request_gate,
    retry_after_seconds,
)
from custom_components.my_verisure.core.application.exceptions import (
    MyVerisureServiceBlockedError,
)
from custom_components.my_verisure.core.file_manager import FileManager
from custom_components.my_verisure.core.session_manager import SessionManager


@pytest.fixture
async def gate(monkeypatch):
    clock = SimpleNamespace(monotonic=1000.0, wall=1800000000.0)
    value = ProviderRequestGate(
        monotonic=lambda: clock.monotonic,
        wall_clock=lambda: clock.wall,
    )
    monkeypatch.setattr(
        asyncio.get_running_loop(),
        "_my_verisure_provider_request_gate",
        value,
        raising=False,
    )
    return value, clock


class Response:
    def __init__(self, status=200, retry_after=None, entering=None, body=None):
        self.status = status
        self.headers = {} if retry_after is None else {"Retry-After": retry_after}
        self.entering = entering
        self.json = AsyncMock(
            return_value={"data": {"ok": True}} if body is None else body
        )

    async def __aenter__(self):
        if self.entering is not None:
            raise self.entering
        return self

    async def __aexit__(self, *_args):
        return False


@pytest.fixture
def http(monkeypatch):
    responses = []
    sessions = []

    def factory(**_kwargs):
        response = responses.pop(0)
        session = SimpleNamespace(closed=False, post=Mock(return_value=response))

        async def close():
            session.closed = True

        session.close = AsyncMock(side_effect=close)
        sessions.append(session)
        return session

    mocked = Mock(side_effect=factory)
    monkeypatch.setattr(base_client.aiohttp, "ClientSession", mocked)
    return responses, sessions, mocked


async def test_legacy_block_stops_before_creating_http_session(gate, http):
    manager = SimpleNamespace(is_service_blocked=lambda: True)
    with pytest.raises(MyVerisureServiceBlockedError):
        await BaseClient(manager)._execute_query_direct("mutation synthetic")
    http[2].assert_not_called()


async def test_shared_block_stops_different_clients_and_entries(gate, http):
    shared, clock = gate
    shared.record_blocked("120")
    managers = (
        SimpleNamespace(),
        SimpleNamespace(is_service_blocked=lambda: False),
    )
    for manager in managers:
        with pytest.raises(MyVerisureServiceBlockedError):
            await BaseClient(manager)._execute_query_direct("query synthetic")
    http[2].assert_not_called()
    clock.monotonic += 121
    http[0].append(Response())
    result = await BaseClient(SimpleNamespace())._execute_query_direct(
        "query synthetic"
    )
    assert result == {"data": {"ok": True}}


@pytest.mark.parametrize("status", [403, 429])
async def test_rate_limit_blocks_next_entry_without_retrying_mutation(
    gate,
    http,
    status,
    caplog,
):
    response = Response(status, "120")
    http[0].append(response)
    manager = SimpleNamespace(record_service_blocked=Mock())
    first = BaseClient(manager)
    second = BaseClient(SimpleNamespace())
    with pytest.raises(MyVerisureServiceBlockedError):
        await first._execute_query_direct(
            "mutation synthetic",
            headers={"auth": "synthetic-private-value"},
        )
    with pytest.raises(MyVerisureServiceBlockedError):
        await second._execute_query_direct("query synthetic")
    assert len(http[1]) == 1
    http[1][0].post.assert_called_once()
    http[1][0].close.assert_awaited_once()
    response.json.assert_not_awaited()
    manager.record_service_blocked.assert_called_once_with(120.0)
    assert "synthetic-private-value" not in caplog.text


@pytest.mark.parametrize("status", [403, 429])
async def test_real_entry_managers_keep_local_compatibility_and_share_admission(
    gate,
    http,
    tmp_path,
    status,
):
    first = SessionManager(file_manager=FileManager(tmp_path / "first"))
    second = SessionManager(file_manager=FileManager(tmp_path / "second"))
    http[0].append(Response(status))
    with pytest.raises(MyVerisureServiceBlockedError):
        await BaseClient(first)._execute_query_direct("query first")
    assert first.is_service_blocked()
    with pytest.raises(MyVerisureServiceBlockedError):
        await BaseClient(second)._execute_query_direct("query second")
    assert len(http[1]) == 1


@pytest.mark.parametrize(
    "header",
    [
        None,
        "nonsense",
        "-5",
        "NaN",
        "1.5",
        "Wed, 99 Foo 2026 10:00:00 GMT",
    ],
)
def test_invalid_retry_after_uses_conservative_default(header):
    assert retry_after_seconds(header, 1800000000.0) == 600.0


def test_retry_after_accepts_numeric_and_utc_http_date():
    now = 1800000000.0
    future = format_datetime(
        datetime.fromtimestamp(now + 1800, timezone.utc),
        usegmt=True,
    )
    assert retry_after_seconds("45", now) == 45.0
    assert retry_after_seconds(future, now) == 1800.0
    assert retry_after_seconds("0", now) == 0.0
    past = format_datetime(datetime.fromtimestamp(now - 30, timezone.utc), usegmt=True)
    assert retry_after_seconds(past, now) == 0.0


async def test_http_date_and_invalid_date_enforce_block_before_http(gate, http):
    shared, clock = gate
    future = format_datetime(
        datetime.fromtimestamp(clock.wall + 1800, timezone.utc),
        usegmt=True,
    )
    http[0].append(Response(429, future))
    with pytest.raises(MyVerisureServiceBlockedError):
        await BaseClient(SimpleNamespace())._execute_query_direct("query synthetic")
    assert shared.remaining_seconds == 1800.0
    clock.monotonic += 1801
    http[0].append(Response(403, "invalid date"))
    with pytest.raises(MyVerisureServiceBlockedError):
        await BaseClient(SimpleNamespace())._execute_query_direct("query synthetic")
    assert shared.remaining_seconds == 600.0


async def test_shorter_header_does_not_clear_existing_deadline(gate):
    shared, clock = gate
    shared.record_blocked("1800")
    clock.monotonic += 10
    shared.record_blocked("1")
    assert shared.remaining_seconds == 1790.0


async def test_concurrent_requests_are_serialized_and_recheck_block(gate, http):
    entered, release = asyncio.Event(), asyncio.Event()

    class BlockingResponse(Response):
        async def __aenter__(self):
            entered.set()
            await release.wait()
            return self

    http[0].append(BlockingResponse(429, "120"))
    first = asyncio.create_task(
        BaseClient(SimpleNamespace())._execute_query_direct("query one")
    )
    await entered.wait()
    second = asyncio.create_task(
        BaseClient(SimpleNamespace())._execute_query_direct("query two")
    )
    await asyncio.sleep(0)
    assert len(http[1]) == 1
    release.set()
    results = await asyncio.gather(first, second, return_exceptions=True)
    assert all(isinstance(result, MyVerisureServiceBlockedError) for result in results)
    assert len(http[1]) == 1


async def test_cancellation_waiting_for_gate_creates_no_http_session(gate, http):
    shared, _clock = gate
    async with shared.async_request():
        task = asyncio.create_task(
            BaseClient(SimpleNamespace())._execute_query_direct("query waiting")
        )
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        http[2].assert_not_called()
    http[0].append(Response())
    await BaseClient(SimpleNamespace())._execute_query_direct("query following")


async def test_request_cancellation_closes_session_and_releases_gate(gate, http):
    http[0].extend([Response(entering=asyncio.CancelledError()), Response()])
    with pytest.raises(asyncio.CancelledError):
        await BaseClient(SimpleNamespace())._execute_query_direct("query cancelled")
    http[1][0].close.assert_awaited_once()
    await BaseClient(SimpleNamespace())._execute_query_direct("query next")
    assert len(http[1]) == 2


async def test_operation_state_is_shared_but_does_not_lock_http(gate, http):
    shared, _clock = gate
    state = shared.get_operation_state("synthetic-opaque-namespace")
    assert state is shared.get_operation_state("synthetic-opaque-namespace")
    assert state.generation == 0
    state.generation += 1
    assert shared.get_operation_state("synthetic-opaque-namespace").generation == 1
    http[0].append(Response())
    async with state.lock:
        await BaseClient(SimpleNamespace())._execute_query_direct(
            "query within operation"
        )
    assert not state.publication_lock.locked()


async def test_operation_state_prunes_without_consumer_and_lock_retains_owner(
    gate,
):
    shared, _clock = gate
    state = shared.get_operation_state("synthetic-unused")
    reference = weakref.ref(state)
    del state
    gc.collect()
    assert reference() is None
    first = shared.get_operation_lock("synthetic-lock-only")
    gc.collect()
    assert shared.get_operation_lock("synthetic-lock-only") is first


def test_gate_lifetime_is_local_to_each_event_loop():
    async def create():
        assert get_provider_request_gate() is get_provider_request_gate()
        return get_provider_request_gate()

    first, second = asyncio.run(create()), asyncio.run(create())
    assert first is not second

# Notification implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Correct the audited defects, then implement the approved notification observability and automation contract without losing photo completion, identity or polling fallback.

**Architecture:** Provider adapters decode/map bounded input; an entry-owned application notification module applies routing, replay and lifecycle policy. HA projects reported and verified records to separate event entities. A shared origin gate and installation operation generation protect provider requests and snapshot publication.

**Tech Stack:** Python 3.14, asyncio, existing firebase-messaging 0.4.5 adapter, aiohttp, HA EventEntity, pytest/real HA fixtures, mypy and architecture/distribution gates.

Execution is authorized inline, with bounded delegated file ownership. Existing
research edits belong to this iteration. No native/HA alarm-total tests are allowed.
No live alarm command is necessary to implement or verify these contracts.

## 1. Correct request admission and snapshot ordering

Files: `core/api/base_client.py`, proposed `core/api/provider_request_gate.py`,
`core/session_manager.py` as needed, `coordinator.py`, `core/api/alarm_client.py`
and dedicated synthetic regressions under `core/tests/unit/` and `tests/`.

- [x] Reproduce cooldown/429 and old-read overwrite with actual methods/fake transports; assert zero real sessions/commands.
- [x] Add shared origin gate with per-installation operation state (lock, publication lock, generation); gate before constructing HTTP sessions.
- [x] Handle 403/429 and bounded Retry-After without mutation replay. Keep gate ownership only for each wire request.
- [x] Serialize complete commands; prevent older targeted/full reads publishing after newer state.
- [x] Add `AlarmClient.get_current_alarm_status` and coordinator `async_refresh_current_alarm_state() -> dict | None`, with no radio/full-refresh/cache fallback.
- [x] Run focused regressions and inspect failure-to-pass evidence.

Required assertions include:

```python
assert fake_http.post.call_count == 0  # cooldown already active
assert confirmed_snapshot == snapshot_after_older_read_finishes
assert not fake_check_alarm.called  # native state unknown
```

## 2. Correct receiver recovery and durable write ownership

Files: `core/api/push_storage.py`, `push_receiver.py`, `push_decoder.py` if
necessary, and their existing/new unit tests.

- [x] Add failing canceled-write ordering and corrupt cached-key regressions.
- [x] Retain strong ownership and serialization until an executor write finishes, even when its caller is canceled.
- [x] Validate cached P-256 private/public correspondence and the decoded authentication secret; retain zero-HTTP cached startup.
- [x] Bound SDK frame reads before allocation through a small tested adapter override.
- [x] Preserve private 0600 writes, MCS recovery pacing and task draining.
- [x] Run focused tests; review both correction blocks together before feature wiring.

```python
assert await store.load("synthetic.json") == {"version": 2}
assert receiver._cached_token() is None  # malformed crypto
resolver.assert_not_awaited()  # valid durable startup
```

## 3. Typed records and provider mapping

Files: proposed `core/application/notifications.py`,
`core/api/notification_mapper.py` and independent unit tests.

- [x] Add red tests for every declared source request family, invalid JSON/shape/size, recipient mismatch, unknown scope and bounded timestamps.
- [x] Implement immutable public event records with safe finite types, opaque IDs, separate receipt/occurrence/verification time and reported/confirmed stage.
- [x] Keep raw signal/operation data private to typed consumers; never project arbitrary text/URLs/account identifiers.
- [x] Centralize bounded replay, diagnostic ring, readiness buffering and once-per-delivery fan-out, preserving direct pending-photo wake-up.
- [x] Test unknown/future/stale/missing time, duplicates, buffer overflow, consumer failure and unsubscribe/close.

```python
assert record.kind == "alarm_operation_reported"
assert record.stage == "reported"
assert "advancedInfo" not in record.public_data()
assert hub.accept(payload, delivery_id) is None  # duplicate
```

## 4. Read scheduling and authoritative consumers

Files: proposed `core/application/notification_refresh.py`, provider incident
adapter, existing photo/use-case adapters and coordinator composition.

- [x] Write red burst/coalescing/cooldown/cancellation tests with injected clocks.
- [x] Implement a finite resource queue, two-second grouping and conservative 30-second background start budget shared across the origin/account scope.
- [x] Invoke only native current-state reads or documented incident reads; unknown categories never create work.
- [x] Emit state facts only from new authoritative semantic changes or live correlated operation results; suppress initial/recovery automation replay.
- [x] Publish `photo_ready` after all image writes and completion marker; preserve exact-signal validation and the 20-second polling fallback.
- [x] Add opt-in external photo retrieval using existing signal reads, without ever creating another capture.
- [x] Treat missing entitlement/schema as unavailable capability, not fabricated support; register/bind token recovery without automatic repeated SMS.

```python
assert pending_resource_count == 1  # one resource, many notices
assert fake_mutations == []
assert photo_ready_events == []  # any expected write failed
```

## 5. HA platforms, options, diagnostics and automation contract

Files: proposed `event.py`, `integration.py`, `push.py`, `config_flow.py`,
`core/const.py`, `sensor.py`, `binary_sensor.py`, `diagnostics.py`, strings and
translations, plus real HA platform/lifecycle fixtures.

- [x] Add two EventEntities with stable entry-scoped identities; subscribe before draining presentation and detach on unload.
- [x] Keep event availability independent of MCS/GraphQL availability and retain the first genuine event after reconnect.
- [x] Add precise transport/binding/accepted/rejected/replay/overflow/authoritative-sync diagnostics and category coverage.
- [x] Add approved opt-in selective refresh/external-photo/bus options, preserving existing push and polling defaults.
- [x] Mirror the same safe record on the optional advanced bus; restore display without new live emissions.
- [x] Validate actual EventEntity restore, first event, rapid repeated events, multi-entry isolation, disabled entities and safe Recorder-facing attributes.
- [x] Add complete documented automation examples/blueprints using event.received and explicit stage/type selection; no alarms are executed by examples or tests.

## 6. Complete verification, documentation and controlled installation

- [x] Run all deterministic tests and release gates in the pinned environment. Measure changed-module branch coverage and close meaningful gaps; do not equate old repository aggregate coverage with new-code coverage.
- [x] Update the SDD/catalog from proposal to implemented behavior, preserving non-photo live-delivery evidence limits. Record actual supported/observed categories.
- [x] Review the integrated diff for async ownership, sensitive fields, request scope and backwards compatibility.
- [x] Build a production-only artifact, retain the current private rollback and validate HA configuration before restart.
- [x] Install through the established HA workflow. Verify new entities/identity, restore/reconnect, logs and one conservatively spaced photo completion; no alarm changes are needed.
- [x] Keep ordinary polling enabled and leave unrelated app/device registrations untouched.
- [x] Close owned temporary outputs while retaining minimal verification evidence and rollback.

Final evidence: 1,358 tests; ten notification modules at 100% executable line and
branch coverage; 298 typed source files; critical lint, full new-file style,
architecture and production distribution checks passed. HA 2026.11.2 verified
153 installed files and a 23.22-second, three-image FCM capture. The two event
entities and six diagnostics were registered; the original twenty identities,
native UUID and token survived restart/reload. Zero agent alarm commands.

The [implementation receipt](../../validation/2026-11-23-notification-implementation.json)
separates source, synthetic, platform and household evidence. Local cleanup
verified 649 protected inputs and removed generated caches, coverage intermediates
and superseded artifacts; one exact release and the private HA rollback remain.

Commands (use narrow selections for red/green, full gates after integration):

```bash
TMPDIR=/private/tmp HA_PYTHON=/private/tmp/my-verisure-validation-venv/bin/python HA_CORE='' ./scripts/test-ha-2026.8.sh
make type-check lint-critical git-check distribution-check HA_PYTHON=/private/tmp/my-verisure-validation-venv/bin/python
TMPDIR=/private/tmp make coverage HA_PYTHON=/private/tmp/my-verisure-validation-venv/bin/python
```

Expected final results: complete suite/gates pass, new scenario/branch gaps are
reported accurately, HA runtime evidence is distinct from synthetic results, and
no new notification-to-command path or hidden polling acceleration exists.

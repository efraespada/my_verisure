# Coordinator structural refactor plan — 2026-08-13

## Objective

Reduce the remaining `MyVerisureDataUpdateCoordinator` hotspot while preserving
Home Assistant lifecycle behavior, entry-scoped composition, public coordinator
methods, and all provider/result contracts.

## Baseline

- `coordinator.py`: 502 lines.
- Repowise hotspot health: 4.29.
- Full suite before this iteration: 437 passed, 2 skipped, 81% coverage.
- Existing application boundaries: authentication policy, snapshot service/store,
  failure classifier, alarm command metadata, translation service, and camera
  use cases.

## Constraints

- No provider calls or household Home Assistant instance.
- No compatibility shims or cosmetic line splitting.
- Every slice must add or preserve characterization tests.
- Run focused tests, mypy, critical Flake8, and diff checks before each push.
- Commit and push each validated slice.

## Slices

### 1. Refresh result persistence boundary

Extract the post-refresh effects currently embedded in `_async_update_data` and
`_async_refresh_alarm_only`:

- publish coordinator data;
- persist the snapshot;
- create dummy camera images where applicable;
- report persistence failures without changing returned data.

Keep orchestration decisions in the coordinator and make the boundary injectable
and unit-testable.

### 2. Camera refresh orchestration boundary

Extract camera refresh policy/configuration:

- default polling values;
- entry-scoped installation id;
- result logging;
- failure handling contract.

Keep `async_refresh_camera_images()` as the HA adapter method.

### 3. Notification and failure effects

Extract the HA notification effect boundary:

- translation lookup;
- persistent notification creation;
- stable notification IDs;
- service-blocked and alarm-command notifications.

The coordinator will retain failure classification and HA exception mapping, but
will not build notification payloads inline.

### 4. Session lifecycle boundary

Review `async_login`, `async_refresh_session`, `async_load_session`, and the
session convenience methods. Extract only cohesive policy or result mapping;
keep Home Assistant auth exceptions at the coordinator boundary.

### 5. Final verification

Run focused and full suites, coverage, mypy, critical lint, compileall,
architecture guard, pip check, Repowise, and tree/branch synchronization. Update
this plan with exact evidence and explicit limitations.

## Acceptance criteria

- No regression in HA lifecycle, service dispatch, snapshot fallback, or auth
  behavior.
- Coordinator public methods remain compatible.
- Each extraction has direct unit coverage.
- `master` equals `origin/master` and the working tree is clean.
- Residual Coordinator size/hotspot is reported honestly; no claim that it is
  fully eliminated unless verified.

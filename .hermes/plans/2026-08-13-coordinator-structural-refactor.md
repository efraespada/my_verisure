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

## Execution result — Coordinator structural refactor

Completed slices, each committed and pushed after focused validation:

- `CoordinatorRefreshEffects`: publishes coordinator data, persists the
  entry-scoped snapshot, and optionally creates dummy camera images. Persistence
  and placeholder failures remain non-fatal as before.
- `CoordinatorCameraRefresh`: owns camera polling defaults and result logging;
  `async_refresh_camera_images()` remains a thin HA/dev-mode adapter.
- `CoordinatorNotificationService`: owns translation lookup and persistent
  notification creation; the coordinator retains the decisions and stable IDs.
- `CoordinatorSessionPolicy`: pure session-state decision policy for valid,
  blocked, refreshable, and unavailable states; session I/O remains in the
  coordinator/session manager boundary.

The coordinator fixture tests were updated to declare each new collaborator
explicitly when using `object.__new__`; no dependency was hidden behind a mock.

Evidence:

- Focused slices passed: 12 refresh-effects tests, 16 camera/lifecycle tests, 15
  notification/update tests, and 17 session/lifecycle tests.
- Full suite: 449 passed, 2 skipped.
- Coverage: 82%.
- Mypy: no issues in 206 source files.
- Critical Flake8, compileall, architecture guard, pip check, and diff checks:
  all passed.
- Coordinator size: 502 → 499 lines.
- Repowise hotspot health: 4.29 → 4.31.
- Repowise maintainability average: 9.25 → 9.26.
- Repowise worst hotspot is now `AlarmClient`, not `Coordinator`.

The coordinator still contains HA lifecycle wiring, provider failure mapping,
command adapters, and session I/O adapters. Those were intentionally retained
at the composition/HA boundary rather than moved into artificial wrappers.
Manual Docker HA and real-provider validation remain unavailable and were not
represented as passed.

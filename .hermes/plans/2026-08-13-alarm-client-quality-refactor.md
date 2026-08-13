# AlarmClient quality refactor — 2026-08-13

## Goal

Reduce `AlarmClient` through real cohesive boundaries while preserving the
provider contract, Home Assistant integration behavior, entry-scoped
credentials, redacted logging, and current public client methods.

## Baseline

- `AlarmClient`: 672 lines.
- Repowise hotspot health: 4.36.
- Worst performer: `custom_components/my_verisure/core/api/alarm_client.py`.
- Full suite: 457 passed, 2 skipped.
- Mypy: 209 files without errors.
- Existing boundaries: request policy, command poller, command response
  interpreter, realtime status interpreter.

## Iterations

### 1. Status configuration boundary

Extract the alarm status configuration loading and message-to-status mapping
into an application service with explicit input/output types. It must own the
cache and fallback configuration, use injected file-loading behavior where
needed for tests, and never depend on `AlarmClient` or provider transport.

### 2. Realtime status workflow

Extract the CheckAlarm → reference ID → polling → message interpretation flow
into a coordinator/application service. The service receives credentials and a
transport port/callback, returns a typed status outcome, and owns retry policy.
`AlarmClient` remains the adapter that supplies transport and translates the
outcome to its current public dictionary contract.

### 3. Command execution workflow

Review arm/disarm orchestration after the status extraction. If a cohesive
command workflow can be extracted without merely forwarding every argument,
move response acceptance, reference validation, and poll transport ownership
behind an application boundary. Keep GraphQL request construction in the
existing request policy.

### 4. Contracts and verification

Add unit tests for each new pure/application boundary, including malformed
responses, missing references, provider errors, wait exhaustion, credentials,
and concurrent client instances. Preserve existing client contract tests and
HA service behavior.

### 5. Gates and documentation

Run the full suite, Home Assistant 2026.8.1 suite, mypy, critical Flake8,
compileall, architecture guard, pip check, diff check, and Repowise. Update
this plan with measured results and explicit limitations. Commit and push each
validated iteration.

## Execution result

The refactor was executed in three validated iterations:

### Iteration 1 — alarm status configuration

Published as `be5de8a refactor: isolate alarm status service`.

- Added `AlarmStatusService` in the application layer.
- Moved configuration loading, per-instance caching, safe fallback, default
  status construction, and message matching out of `AlarmClient`.
- Preserved the existing private client entry points as thin application-boundary
  calls so current internal contracts remain stable.
- Added direct tests for internal/external matching, empty messages, caching,
  invalid JSON, and missing files.

### Iteration 2 — realtime status workflow

Published as `64ed130 refactor: isolate realtime alarm status workflow`.

- Added `RealtimeAlarmStatusWorkflow`.
- Moved retry count, wait policy, delay injection, terminal response handling,
  and transport-failure normalization out of the API adapter.
- Kept `RealtimeAlarmStatusInterpreter` as the pure provider-response parser.
- `AlarmClient` now only supplies the GraphQL transport callback.

### Iteration 3 — arm/disarm command workflow

Published as `69f1288 refactor: isolate alarm command workflow`, followed by
`85bfb6c test: align alarm workflow contract`.

- Added `AlarmCommandWorkflow` with explicit `arm()` and `disarm()` operations.
- Moved initial response acceptance, reference validation, status transport
  factory creation, and polling delegation out of `AlarmClient`.
- Preserved separate arm/disarm payload contracts; no reflection or generic
  command shim was introduced.
- Fixed and tested the contract that an `OK` provider response without a
  `referenceId` is a failure with `Missing command reference`.

## Measured result

- `AlarmClient`: `672 → 537` lines.
- Repowise hotspot health: `4.36 → 4.47`.
- Repowise worst performer changed from `AlarmClient` to `AuthClient`.
- Maintainability average: `9.26 → 9.30`.
- Full suite: `457 → 471` passed tests.
- Coverage: `82% → 83%`.

## Verification

- `make ci`: `471 passed, 2 skipped`.
- `make test-ha-2026-8`: `471 passed, 2 skipped` on Home Assistant Core
  2026.8.1 / Python 3.14.4.
- Mypy: no issues in 215 source files.
- Critical Flake8: passed.
- `compileall`: passed.
- `ARCHITECTURE_GUARD_OK`.
- `pip check`: no broken requirements.
- `git diff --check`: passed.

## Remaining boundary

`AlarmClient` remains an external API adapter and still owns GraphQL request
transport, entry-scoped credentials, redacted logging, and direct request
builders. Those are intentional adapter responsibilities. Further extraction
should only happen when another provider-facing contract is independently
cohesive; reducing the line count alone is not a sufficient reason.

No real Verisure calls or manual Docker Home Assistant validation were claimed.

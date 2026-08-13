# Coverage and hotspot reduction plan — 2026-08-13

## Objective

Raise meaningful behavioral coverage and reduce production hotspot risk without
chasing 100% mechanically, changing external behavior, or adding compatibility
shims. Every slice must have a focused regression test, full gates, and its own
commit/push.

## Baseline

- HA Core 2026.8.1 / Python 3.14.4.
- 361 passed, 2 skipped.
- Total coverage: 73%.
- Lowest-risk production coverage: AuthClient 11%, CameraClient 12%, Coordinator
  21%, ConfigFlow 43%, services 53%.
- Repowise hotspots: Coordinator, AlarmClient, AuthClient, CameraClient and
  ConfigFlow. Repowise is advisory and does not replace behavioral tests.

## Iteration A — Authentication boundary

1. Characterize login success, GraphQL errors, malformed success payloads,
   missing session hash, device authorization and OTP transitions.
2. Characterize OTP send/verify, phone selection and session updates.
3. Extract pure response classification only if it reduces coupling and is
   protected by tests; otherwise keep the adapter stable and improve tests.
4. Acceptance: no secrets in logs, entry-scoped session remains explicit, focused
   tests pass, mypy/lint remain green.

## Iteration B — Camera boundary

1. Characterize request-image validation, GraphQL errors, existing-request retry,
   status exhaustion, malformed payloads, thumbnail/photo mapping and persistence.
2. Extract response classification/polling only where it removes duplicated
   protocol logic without hiding provider failures.
3. Acceptance: explicit failure DTOs for every terminal path and no leaked auth
   headers/capabilities in logs.

## Iteration C — HA adapter coverage

1. Add tests for coordinator auth/cache/connection/service-blocked paths.
2. Add ConfigFlow reauth/options/duplicate/error tests.
3. Add service registration, unavailable coordinator, result mapping and unload
   tests.
4. Add only high-value platform state/availability tests.

## Iteration D — Final risk review

1. Re-run Repowise and classify findings as actionable, intentional, or false
   positive; do not refactor tests solely to satisfy duplication metrics.
2. Run full suite, contextual coverage, mypy, lint, architecture, dependencies,
   imports and diff checks.
3. Keep real-provider and Docker/manual HA validation explicitly separate.

## Final status for this iteration

Completed and pushed:

- authentication response classification extracted into a pure application
  service, with protocol branch characterization;
- camera request/polling and image persistence branches characterized;
- HA ConfigFlow OTP/error/lifecycle branches covered;
- Coordinator cache, authentication, connection and service-blocked boundaries
  covered;
- alarm service dispatch boundaries covered.

Measured result: 390 passed, 2 skipped, 77% total coverage. Hotspot coverage
improved substantially without changing external contracts. Repowise remains
advisory: Coordinator and AlarmClient still deserve future decomposition, but a
large uncharacterized rewrite is intentionally deferred. Docker/manual HA and
real Verisure remain outside this deterministic test run.


- All focused tests cover critical error and lifecycle branches.
- Coverage improves from 73% through behavior, not trivial line execution.
- No new ignores, global fallback, secret logging or unsupported HA compatibility.
- All commits pushed; `master == origin/master`; clean tree.

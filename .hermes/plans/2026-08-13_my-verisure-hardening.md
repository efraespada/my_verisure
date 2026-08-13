# My Verisure Clean Architecture Hardening Plan

**Goal:** Complete the remaining Clean Architecture, Home Assistant 2026.8 validation, coverage, and release-readiness work without weakening the existing contracts.

**Architecture:** Keep Home Assistant modules as thin adapters. Keep domain models and use cases independent from HA. Make every runtime dependency entry-scoped through `CompositionRoot`; remove legacy global fallbacks rather than extending them. Decompose the coordinator and Verisure clients only behind characterization tests and explicit ports.

## Baseline

- Target runtime: Home Assistant Core 2026.8.1, Python >=3.14.2.
- Current validation: 326 passed, 2 skipped against HA 2026.8.1; legacy Python 3.11 suite also passes.
- Current risks: global fallback paths, module-level DeviceManager cache, large Coordinator/AlarmClient, weak coverage in HA platforms/config flow/services and API clients.
- No real credentials or external Verisure calls are permitted in automated tests.

## Iteration 0 — Audit and guardrails

1. Run Repowise update/context/health and record current hotspots.
2. Add/refresh architecture decisions for entry-scoped composition and no-global-state migration.
3. Keep the legacy `.venv` and modern HA target environment separate.
4. Commit only verified documentation/guardrail changes.

## Iteration 1 — DeviceManager scope and deterministic identity support

1. Add characterization tests for synchronous/asynchronous load/save, generated identifiers, and two independent managers.
2. Remove module-level `_cached_platform_string` and `global` usage; inject a small platform-information provider or keep the cache on the manager instance.
3. Make `FileManager` mandatory and remove compatibility fallback wording.
4. Ensure the DI module is the only production construction path.
5. Run focused tests, full suite, architecture guard, mypy scope, and HA target tests.
6. Commit and push.

## Iteration 2 — Close manager/client dependency boundaries

1. Inventory all remaining global access and fallback branches.
2. Migrate LogManager, ConfigManager, BaseClient, CameraClient, and any repositories/adapters to mandatory constructor dependencies.
3. Remove fallback constructors only after all callers/tests use the explicit graph.
4. Add negative tests proving missing dependencies cannot silently resolve global state.
5. Run full gates and commit/push.

## Iteration 3 — HA adapter contract coverage

1. Add tests for every platform setup: sensor, binary_sensor, alarm_control_panel, button, camera, and device.
2. Assert entity identity, availability, device information, supported features, state/attributes, and unload behavior.
3. Expand config-flow tests for valid input, invalid/auth/network failures, duplicate entries, reauth, and options flow.
4. Expand service tests for every registered service, bad entry, unavailable coordinator, result/error mapping, and two-entry isolation.
5. Run all tests against HA 2026.8.1 and commit/push.

## Iteration 4 — Coordinator boundary decomposition

1. Add characterization tests for refresh, cached fallback, auth failure, connection failure, service-blocked behavior, alarm commands, camera refresh, and cleanup.
2. Extract application-facing refresh/session orchestration ports from `coordinator.py`.
3. Move translation, persistence/cache, and command result handling into focused collaborators.
4. Leave the HA `DataUpdateCoordinator` as an adapter delegating to application ports.
5. Keep behavior identical; no cosmetic extraction.
6. Run complexity/coverage checks, Repowise risk/context, full tests, and commit/push.

## Iteration 5 — AlarmClient boundary decomposition

1. Add characterization tests for GraphQL/direct transport success, malformed responses, errors, polling exhaustion, arm/disarm outcomes, and redacted logging.
2. Extract transport and response interpretation behind explicit ports.
3. Keep `AlarmClient` as a focused application/API adapter, not a parser, poller, logger, and command dispatcher simultaneously.
4. Remove duplication only when tests protect each response contract.
5. Run full gates, Repowise, and commit/push.

## Iteration 6 — Modern HA test automation and release verification

1. Add a reproducible `make test-ha-2026-8` target using Python 3.14 and `requirements-ha-2026.8.txt` without contaminating `.venv`.
2. Add CI coverage for the modern target where runner support permits; keep legacy/unit gates explicit.
3. Document installation, update, unload, and manual HA verification steps.
4. Run complete suite, coverage with test contexts, Repowise impacted-tests, security scan, architecture guard, mypy, lint, and diff checks.
5. Commit/push only with a clean tree and verifiable output.

## Definition of done

- No production runtime path silently falls back to global managers/injectors.
- Composition is explicit and isolated per `ConfigEntry`.
- HA 2026.8.1 tests cover lifecycle, platforms, config flow, services, errors, and isolation.
- Coordinator and AlarmClient have explicit boundaries and materially reduced complexity.
- Modern HA test command is reproducible and documented.
- All gates pass with reports based on real execution.
- Real-account validation remains a separate manual step and is never claimed without executing it.

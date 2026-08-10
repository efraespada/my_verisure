# Multi-area Clean Architecture Quality Plan

## Baseline

- Repository: `efraespada/my_verisure`
- Branch: `master`
- Starting commit: `2134289`
- Working tree: clean
- Verified baseline: `275 passed, 2 skipped`; architecture guard green; critical Flake8 green; incremental mypy green; global coverage `58%`.

## Progress

- [x] Baseline and multi-area plan recorded.
- [x] Alarm dispatcher application boundary implemented and connected to `arm_away`.
- [x] Explicit isolated `CompositionRoot` implemented and unit-tested.
- [x] Composition root owns explicit per-entry `SessionManager` and `FileManager` instances.
- [x] Route `InstallationClient`, `AlarmClient`, and `CameraClient` through the entry-scoped session manager.
- [x] Correct legacy `AlarmClient` response typing and empty-message contract.
- [x] Migrate `CameraClient` from global `FileManager` lookup to entry-scoped ownership.
- [x] Migrate `DeviceManager` from global `FileManager` lookup.
- [x] Migrate `LogManager` and `ConfigManager` from global manager ownership.
- [x] Migrate `InstallationRepositoryImpl` cache storage to entry-scoped `FileManager`.
- [x] Migrate coordinator and integration runtime callers from global managers.
- [x] Migrate camera entity and dummy-image use case from global file manager.
- [x] Migrate `config_flow.py` and remaining session-manager callers from global injector.
- [ ] Replace `SessionManager` auto-reauth global provider usage with an injected auth boundary.
- [x] Disarm service contract audited: the HA `code` field was removed because the
  Verisure GraphQL disarm contract does not accept or forward it.
- [ ] Complete remaining alarm service handlers through the application dispatcher.
- [x] Camera refresh use-case return type aligned with its concrete `CameraRefresh` result.
- [x] Coordinator translation loader annotated as JSON text, matching runtime behavior.
- [ ] Classify and address remaining incomplete/TODO production paths.
- [ ] Complete bounded typing/lint batches and final release gates.

## Principles

- Preserve Home Assistant public service names, schemas, entity IDs, and runtime behavior.
- No compatibility shims for obsolete contracts.
- No network calls in unit tests; use application ports and deterministic fakes.
- No mutation of production behavior without a failing test first.
- Keep HA adapters thin: validate/translate/dispatch; keep business decisions in Core.
- Avoid new global state; dependencies enter through an explicit composition boundary.
- Treat every `TODO`/`pass` as a hypothesis to classify before implementation.
- Commit and push only after the relevant slice and full regression gates are green.

## Areas and vertical slices

### A. Service application boundary

1. Map each HA service to its coordinator/use-case operation.
2. Add failing tests for success, domain failure, exception, and missing installation.
3. Extract a typed application service/dispatcher port if the contract is stable.
4. Keep `services.py` responsible only for schema data and HA registration.
5. Verify all six public services and unload behavior.

### B. Composition root and dependency injection

1. Document the current construction graph and global state.
2. Add a failing test for deterministic construction of a single config-entry graph.
3. Introduce an explicit composition object/factory at the integration boundary.
4. Inject clients, repositories, use cases, and coordinator dependencies.
5. Preserve config-entry isolation and unload semantics.
6. Remove global injector dependence only after all callers migrate.

### C. Contract typing and error boundaries

1. Inventory remaining mypy errors by layer.
2. Define typed result/error boundaries for coordinator and HA adapters.
3. Replace `Any` at Core boundaries with DTO/domain types where evidence supports it.
4. Add negative/error-path tests before changing behavior.
5. Run incremental mypy per bounded package.

### D. Incomplete/TODO audit

1. Classify interface `pass`, intentionally unsupported platform features, and real unfinished production paths.
2. For real gaps, create one test-first vertical slice at a time.
3. For intentional unsupported behavior, document the boundary and add a regression test.
4. Do not implement arbitrary camera streaming or unrelated speculative features.

### E. Quality and documentation

1. Reduce Flake8 debt only in files touched by the current slice.
2. Keep critical Flake8 gate mandatory for the whole repository.
3. Measure global and per-module coverage after each slice.
4. Update the architecture audit with facts, limitations, and remaining debt.
5. Run full tests, compileall, architecture guard, critical lint, incremental mypy, diff checks.
6. Commit and push each verified vertical slice.

## Iteration protocol

For every production change:

1. Write one focused failing test.
2. Run it and confirm the expected failure.
3. Implement the smallest production change.
4. Run the focused test.
5. Refactor only after green.
6. Run the affected package suite.
7. Run the complete gates before commit/push.

## Stop conditions

Stop and reassess architecture instead of stacking fixes when:

- three different fixes fail for the same seam;
- a change requires restoring obsolete API aliases;
- a service handler requires direct network/file access in the HA adapter;
- composition introduces a new singleton/global registry;
- tests need real credentials or a live Verisure API.

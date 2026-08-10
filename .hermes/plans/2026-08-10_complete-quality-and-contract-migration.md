# Complete Clean Architecture and Quality Plan

## Scope

Repository: `efraespada/my_verisure`

The goal is to close the remaining migration debt after the domain/DTO boundary
extraction, without adding compatibility shims for obsolete APIs.

## Baseline

- Runtime: Python 3.11, repository `.venv`.
- Core unit suite after migration: `229 passed`.
- Application/CLI/integration suite: `39 passed, 2 skipped`.
- Combined coverage run: `268 passed, 2 skipped`, total `56%`.
- Incremental type gate for DTO/domain/mapper layer: `25 source files`, no issues.
- Critical Flake8 gate (`E9,F63,F7,F82`): passes.
- Full Flake8 baseline: `1121` findings.
- Full mypy baseline after canonical package selection: `99` errors.

## Phase 1 — Contract inventory and classification

- [x] Capture the complete failure list in a reproducible report.
- [x] Classify each failure as current-contract, obsolete-contract, production bug,
      environment/dependency issue, or test isolation issue.
- [x] Define canonical contracts from interfaces, implementations, current CLI,
      and Home Assistant integration consumers.
- [x] Remove/rewrite only tests proven obsolete; preserve behavior tests that expose
      production defects.

## Phase 2 — Repository and use-case contracts

- [x] Migrate alarm repository tests to `get_alarm_status(installation_id, panel,
      capabilities)` and the explicit arm/disarm operation ports.
- [x] Migrate authentication repository tests to the current request/result objects.
- [x] Migrate camera repository tests to mapper-based DTO boundaries.
- [x] Migrate installation repository fixtures to `DetailedInstallationDTO`'s
      current nested contract.
- [x] Repair use-case fixtures and constructor signatures for alarm, camera, and
      installation use cases.
- [x] Add focused application tests for success, failure, and dependency errors.

## Phase 3 — Infrastructure utilities and dependency injection

- [x] Inspect config/file/log/JWT failures separately from architecture migration.
- [x] Fix real production defects only when a current contract demonstrates them.
- [ ] Replace global injector lifecycle with an explicit composition root while
      keeping Home Assistant and CLI entry points stable.
- [x] Add provider contract tests using injected fakes rather than patching private
      module globals.

## Phase 4 — Static quality and packaging

- [x] Add/align lint configuration without hiding existing debt indiscriminately.
- [x] Run Flake8 and classify baseline versus newly introduced issues.
- [x] Add type-check configuration only for supported modules and dependencies.
- [x] Verify runtime/dev dependency declarations and CI parity.
- [x] Add coverage measurement and a documented baseline; no arbitrary threshold
      before the current suite is stable.

## Phase 5 — Documentation and release gates

- [ ] Update architecture audit with final contract decisions.
- [ ] Document canonical test commands and the historical-test migration policy.
- [ ] Run compile, architecture guard, current contract suites, full suite,
      lint/type checks where available, coverage, and diff hygiene.
- [ ] Review the complete diff and report unresolved blockers honestly.

## Completion criteria

The plan is complete only when the current-contract suite, full repository gates,
CI configuration, and documentation agree. Historical tests may be removed or
rewritten only with a recorded reason; failures may not be hidden with blanket
skips or compatibility shims.

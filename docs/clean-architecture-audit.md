# Clean Architecture Audit

## Scope

This audit covers the Python CLI and the Home Assistant custom integration under
`custom_components/my_verisure`.

## Verified baseline (2026-08-10)

- Python compilation: passes for `cli`, `custom_components`, and `scripts`.
- Architecture guard: `ARCHITECTURE_GUARD_OK`.
- Core unit suite after contract migration: `229 passed`.
- Application/CLI/integration suite: `39 passed, 2 skipped`.
- Combined coverage run: `275 passed, 2 skipped`, total coverage `58%`.
- Adapter slice coverage: `sensor.py` `67%`, `integration.py` `44%`, and service
  registration/unload behavior is covered by `test_ha_adapters.py`.
- Incremental mypy gate for domain models, DTOs, and mappers: `25 source files`, no issues.
- Incremental mypy for `sensor.py`, `services.py`, and `integration.py`: no issues.
- Critical Flake8 gate (`E9,F63,F7,F82`): passes.
- Full Flake8 baseline remains `1121` findings, primarily formatting/legacy style debt; it is not suppressed globally.
- Full mypy over the integration currently reports `99` errors after restricting package roots; these are tracked legacy adapter/coordinator/CLI typing debt, not hidden by ignores.
- Coverage gaps are concentrated in Home Assistant service execution branches and coordinator-heavy lifecycle paths.
- The next quality-block adapter changes are validated locally and are pending their own commit/push.
## Findings

### F-001 — Test bootstrap used a non-existent `core/` root

The real package is `custom_components/my_verisure/core`. Runners and setup
scripts referenced `core/tests`, `core/`, and the shell `python` executable.

**Implemented:** runners now use the real paths and `sys.executable`; pytest
also exposes the actual package roots without creating duplicate compatibility
packages.

### F-002 — CLI resolved session state globally (historical baseline)

At the beginning of the migration, commands called `get_session_manager()` inside
operations. This made the CLI difficult to test and encouraged tests to patch
non-existent module attributes.

**Implemented:** `BaseCommand` accepts an explicit session manager and keeps one
session boundary. `AuthCommand` uses the injected boundary. Current production
code and the entry-scoped Home Assistant composition no longer call the global
accessor; the accessor names remain only in the architecture guard as forbidden
patterns and in this historical finding.

### F-003 — Alarm CLI mixed `bool` and result objects

`AlarmCommand._arm` was annotated as returning `ArmResult` but returned `False`
for several branches. That forced callers to handle two incompatible contracts.

**Implemented:** setup, selection, validation, and cancellation failures now
return `ArmResult` values.

### F-004 — Development dependencies were not reproducible

Home Assistant was absent from the local test environment and was not declared
in a development requirements entry.

**Implemented:** added `requirements-dev.txt` using the current
`pytest-homeassistant-custom-component` release available from PyPI at audit
time (`0.13.109`), which pins the Home Assistant test stack for this legacy
integration.

### F-005 — Domain models know transport DTOs

`core/api/models/domain/*` imports `core/api/models/dto/*` and exposes
`from_dto`/`to_dto`. This is the main Clean Architecture violation: domain
objects depend on an outer transport representation.

**Implemented:** authentication, alarm, camera request, session, device, and
installation models are now pure frozen domain values. DTO conversion lives in
mapper modules: `auth_mapper.py`, `alarm_mapper.py`, `camera_mapper.py`,
`session_mapper.py`, `device_mapper.py`, and `installation_mapper.py`.
Their reversible contracts are covered by focused tests. Repository, use-case, DTO,
SessionManager, utility, and dependency-injection suites are now migrated to the
current contracts.

### F-006 — The test tree contains multiple generations of contracts

Examples include old calls to `arm_alarm_away`, old `SessionManager` methods,
old `DetailedInstallation(success=...)` construction, and old DTO
`to_dict()` expectations. These cannot be fixed safely by making production
objects accept every historical signature.

**Migration decision:** classify tests as current-contract, migration-contract,
or obsolete. Current-contract tests become the gate; obsolete tests are
rewritten against the current port/use-case contract rather than hidden.

## Remaining quality work

1. Reduce the tracked Flake8 baseline in small, reviewable batches, starting with
   files touched by the migration; never replace this with a blanket ignore.
2. Type the Home Assistant adapters, coordinator, and CLI result boundaries. The
   current 99-error mypy report is a roadmap, not a passing gate.
3. Add lifecycle tests for `sensor.py`, `integration.py`, and `services.py` before
   raising the 56% coverage baseline.
4. Replace the global injector with an explicit composition-root object after all
   CLI and Home Assistant entry points share the same application graph.

## Target boundaries

```text
CLI / Home Assistant adapter
        -> application use cases and input/output ports
        -> domain entities and policies

API clients / persistence adapters
        -> output ports defined by application

DTOs and Home Assistant objects stay in adapters.
Dependency composition happens once at the composition root.
```

## Execution order

1. Keep runner and import bootstrap deterministic (completed in this slice).
2. Introduce explicit application ports for authentication, installation,
   alarm, and camera operations; leave adapters behind those ports.
3. Move DTO/domain mapping to adapter mapper modules and add contract tests.
4. Replace the global injector lifecycle with a composition-root object that can
   construct an application graph per CLI/HA entry point.
5. Rewrite tests by contract group and delete obsolete historical expectations.
6. Add CI gates for compile, smoke, contract tests, CLI tests, lint, and coverage.
7. Remove transitional import paths and update documentation.

## Acceptance criteria

- No `python`/`pip` shell lookup in project runners; use the active interpreter.
- No nonexistent repository paths in scripts or CI.
- Domain modules import no DTO, CLI, Home Assistant, or HTTP modules.
- Use cases depend only on application ports and domain values.
- Every adapter has contract tests and integration smoke coverage.
- CI fails on collection errors, compile errors, or newly introduced lint errors.
- Historical tests are either migrated with an explicit contract or removed with
  a recorded reason; no blanket skips are used to hide failures.

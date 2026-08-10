# My Verisure Clean Architecture Audit and Migration Plan

> **For Hermes:** Execute this plan incrementally with TDD, preserving verified checkpoints after each slice.

**Goal:** Audit `efraespada/my_verisure` deeply and migrate it toward a real, testable Clean Architecture while repairing the broken test/bootstrap/tooling contracts identified during the initial checkout.

**Architecture:** Keep Home Assistant and CLI modules as outer adapters. Move vendor/API code behind infrastructure adapters, domain models and errors inward, application use cases behind explicit ports, and composition in dedicated factories. Preserve current Home Assistant entity/service behavior and CLI command names unless a breaking change is explicitly required.

**Tech Stack:** Python 3.11, pytest, Home Assistant custom integration, aiohttp, injector, mypy/flake8/black initially; prefer a staged move toward Ruff only if the repository baseline and CI are updated together.

---

## Baseline findings

- Actual production package: `custom_components/my_verisure/`.
- Actual core package: `custom_components/my_verisure/core/`; no root-level `core/` exists.
- CLI package: `cli/`; Home Assistant adapter modules remain at the integration root.
- Large modules: `core/api/alarm_client.py`, `coordinator.py`, `core/api/auth_client.py`, `core/api/camera_client.py`, `config_flow.py`, and `core/session_manager.py`.
- `run_all_tests.py` and `setup_development.py` require obsolete root-level `core/` and therefore cannot execute correctly.
- `requirements.txt` lacks the Home Assistant test/runtime dependency required by integration tests.
- CLI tests contain stale `session_manager` patch/import contracts and behavior mismatches in alarm and display mocks.
- Python bytecode was generated locally by the initial checks but is ignored and must not enter the final diff.
- Current branch is `master`, clean and aligned with `origin/master`.

## Non-negotiable constraints

1. No production refactor without a focused failing test first.
2. Preserve public CLI commands, Home Assistant service names, entity platforms, config-flow behavior, and API semantics unless the change is explicitly documented as breaking.
3. Domain/application code must not import Home Assistant, aiohttp, requests, filesystem helpers, CLI rendering, or vendor DTOs.
4. Infrastructure code owns HTTP, persistence, image files, JWT parsing, and Home Assistant-specific translation.
5. No real Verisure credentials or live calls in tests, logs, fixtures, or documentation.
6. Use `/home/efraespada/my_verisure/.venv/bin/python` for all Python gates.
7. Keep each phase independently reversible and inspect the diff after every slice.

---

## Phase 0 — Baseline and guardrails

### Task 0.1: Add a canonical project test configuration

**Files:**
- Modify: `pytest.ini`
- Create: `conftest.py` only if shared fixtures are proven necessary
- Test: existing test collection

Define test paths explicitly for `cli/tests`, `custom_components/my_verisure/core/tests`, and `custom_components/my_verisure/tests`. Add markers for `unit`, `integration`, and `homeassistant`. Keep collection deterministic.

**Verification:**

```bash
.venv/bin/python -m pytest --collect-only -q
```

### Task 0.2: Record a machine-readable quality baseline

**Files:**
- Create: `docs/quality/baseline.md`
- Create: `docs/quality/architecture-debt.md`

Record current test counts, failures, missing dependencies, largest modules, stale scripts, and the dependency graph. Do not present the baseline as a pass.

### Task 0.3: Add a repository-local quality command

**Files:**
- Create or modify: `Makefile`
- Modify: `AGENT_SETUP.md`
- Modify: `README.md`

Expose canonical commands that always use `.venv/bin/python`: `test`, `test-cli`, `test-core`, `test-ha`, `compile`, `lint`, `typecheck`, and `quality`.

---

## Phase 1 — Repair bootstrap and test collection

### Task 1.1: Fix stale root-path assumptions

**Files:**
- Modify: `run_all_tests.py`
- Modify: `setup_development.py`
- Modify: `run_cli_tests.py`, `run_core_tests.py`, `run_coverage.py`, and `check_coverage.py` where present
- Test: runner smoke tests or subprocess checks

Replace checks for root `core/` with the real `custom_components/my_verisure/core/` path. Centralize path constants instead of duplicating string checks. Ensure subprocesses use `sys.executable`, not ambient `python`.

### Task 1.2: Make dependencies explicit

**Files:**
- Modify: `requirements.txt`
- Create/modify: `requirements-dev.txt` or `pyproject.toml`
- Modify: `.github/workflows/validate.yml`
- Modify: `AGENT_SETUP.md`, `docs/developer-guide/local-development.md`, `docs/developer-guide/testing.md`

Separate runtime, development, and Home Assistant test dependencies. Pin compatible ranges rather than silently relying on a globally installed Home Assistant package. Validate the selected Home Assistant version against the integration manifest and Python 3.11.

### Task 1.3: Repair collection blockers before behavioral refactoring

**Files:**
- Modify: `cli/commands/base.py`, `cli/commands/auth.py`, `cli/utils/__init__.py` as needed
- Modify: `cli/tests/test_session_manager.py` or replace stale imports with the real application port
- Test: focused collection and CLI tests

Decide one canonical session manager location. Prefer the application-facing session port and an injected implementation over module-level imports. Add an import-collection regression before removing any old path.

**Verification:**

```bash
.venv/bin/python -m pytest cli/tests custom_components/my_verisure/core/tests --collect-only -q
```

---

## Phase 2 — Define the real architecture boundaries

### Task 2.1: Introduce dependency-inward packages

**Files:**
- Create: `custom_components/my_verisure/domain/`
- Create: `custom_components/my_verisure/application/`
- Create: `custom_components/my_verisure/infrastructure/`
- Create: `custom_components/my_verisure/composition/`
- Create: `custom_components/my_verisure/presentation/` only for shared HA adapter helpers
- Create: `docs/architecture/dependency-rules.md`
- Test: architecture import checks

Use explicit modules for domain entities/value objects/errors, application ports/use cases, infrastructure implementations, and composition. Do not move files only for appearance; each move must remove an inward dependency or isolate an effect.

### Task 2.2: Move domain models and errors inward

**Files:**
- Source candidates: `core/api/models/domain/*`, `core/api/exceptions.py`
- New canonical files: `domain/models/*`, `domain/errors.py`
- Compatibility re-exports: old model modules where existing imports require them
- Tests: `custom_components/my_verisure/core/tests/unit/test_domain_models.py`, DTO tests, import tests

Domain models must be immutable where practical, vendor-neutral, and free of Home Assistant/aiohttp imports. Keep DTO-to-domain mapping at the infrastructure boundary.

### Task 2.3: Define application ports and use cases

**Files:**
- Create: `application/ports/auth.py`, `application/ports/alarm.py`, `application/ports/installations.py`, `application/ports/cameras.py`, `application/ports/session.py`, `application/ports/files.py`, `application/ports/clock.py`
- Modify/migrate: `core/use_cases/interfaces/*`, `core/use_cases/implementations/*`
- Tests: `custom_components/my_verisure/core/tests/unit/use_cases/*`

Use protocols with domain-level inputs/outputs. No application module may import concrete API clients, Home Assistant coordinators, CLI input/output, or filesystem paths.

### Task 2.4: Add a composition root

**Files:**
- Create: `composition/container.py`
- Modify: `core/dependency_injection/*`
- Modify: `custom_components/my_verisure/__init__.py`, `coordinator.py`, `config_flow.py`, CLI entry points
- Tests: dependency injection and composition tests

Construct configuration, clock, storage, session, clients, repositories, use cases, and HA coordinator through one explicit factory. Importing modules must not open sessions, read credentials, or create files.

---

## Phase 3 — Extract infrastructure adapters vertically

Implement one vertical slice at a time, always RED → GREEN → REFACTOR.

### Task 3.1: Session/authentication adapter

**Files:**
- Source: `core/api/auth_client.py`, `core/session_manager.py`, `core/api/base_client.py`
- Canonical: `infrastructure/verisure/auth_http_client.py`, `infrastructure/session/file_session_store.py`
- Application: `application/use_cases/authenticate.py`, `application/ports/auth.py`, `application/ports/session.py`
- Tests: auth flow, session manager, auth repository/use-case tests

Separate transport/session persistence from authentication orchestration. Sanitize exceptions and ensure credentials/tokens never appear in `repr`, logs, or test output.

### Task 3.2: Installation/device read adapter

**Files:**
- Source: `core/api/installation_client.py`, `core/api/device_manager.py`, `core/repositories/implementations/installation_repository_impl.py`
- Canonical: `infrastructure/verisure/installation_http_client.py`, `infrastructure/repositories/installation_repository.py`
- Tests: installation repository/use case tests

Normalize vendor payloads into domain models once. Add timeout, error classification, and malformed-payload tests.

### Task 3.3: Alarm adapter and commands

**Files:**
- Source: `core/api/alarm_client.py`, `core/api/graphql_alarm_queries.py`, `core/repositories/implementations/alarm_repository_impl.py`, `cli/commands/alarm.py`, `alarm_control_panel.py`, `services.py`
- Canonical: `infrastructure/verisure/alarm_http_client.py`, `application/use_cases/alarm.py`, `presentation/ha/alarm_adapter.py`, `presentation/cli/alarm_commands.py`
- Tests: alarm use case/repository, CLI command tests, HA platform tests

Define typed `ArmResult`/`DisarmResult` semantics consistently and update tests to assert behavior rather than comparing result objects to booleans. Preserve service names and HA state mapping.

### Task 3.4: Camera adapter and file/image ports

**Files:**
- Source: `core/api/camera_client.py`, `core/file_manager.py`, `core/use_cases/implementations/*camera*`, `camera.py`
- Canonical: `infrastructure/verisure/camera_http_client.py`, `infrastructure/filesystem/image_store.py`, `application/use_cases/cameras.py`, `presentation/ha/camera_adapter.py`
- Tests: camera use cases/repository, file manager tests, camera platform tests

Separate download, persistence, cleanup, and HA image serving. Add path traversal, size bounds, overwrite, cleanup, and malformed-image tests.

---

## Phase 4 — Home Assistant adapter and CLI presentation cleanup

### Task 4.1: Keep HA imports at the outer boundary

**Files:**
- Modify: `custom_components/my_verisure/__init__.py`, `config_flow.py`, `coordinator.py`, `alarm_control_panel.py`, `binary_sensor.py`, `button.py`, `camera.py`, `device.py`, `diagnostics.py`, `sensor.py`, `services.py`
- Create: `presentation/ha/*`
- Tests: `custom_components/my_verisure/tests/*`, HA smoke tests

HA modules should translate config/state/events and delegate to application ports/use cases. Remove API/session/filesystem construction from entity modules and coordinator internals.

### Task 4.2: Make CLI a thin adapter

**Files:**
- Modify: `cli/main.py`, `cli/commands/*.py`, `cli/utils/*.py`
- Create: `presentation/cli/*` only if it removes duplicated orchestration
- Tests: `cli/tests/*`

Keep prompts and rendering outside application code. Inject the application facade into commands. Make non-interactive mode deterministic and ensure authentication tests never read stdin unexpectedly.

### Task 4.3: Repair display and mock contracts

**Files:**
- Modify: `cli/utils/display.py`, `cli/tests/test_display.py`, relevant DTO fixtures
- Tests: focused display tests

Define the service DTO shape once. Update mocks to the real contract and cover empty, success, partial, and error states.

---

## Phase 5 — Quality gates and static architecture enforcement

### Task 5.1: Add architecture tests

**Files:**
- Create: `tests/architecture/test_dependency_boundaries.py` or `custom_components/my_verisure/tests/test_architecture.py`
- Create: `scripts/check_architecture.py`
- Modify: `.github/workflows/validate.yml`

Reject domain/application imports of Home Assistant, aiohttp, CLI packages, vendor API modules, filesystem implementation, and concrete DI containers. Validate composition direction.

### Task 5.2: Establish lint and type baselines

**Files:**
- Create/modify: `pyproject.toml` or `setup.cfg`
- Modify: `.github/workflows/validate.yml`
- Modify: `AGENT_SETUP.md`, docs

Configure one canonical lint/format/type toolchain. Start with an explicit baseline for untouched legacy code if necessary, but new/refactored paths must be clean. Avoid hiding errors with broad `# type: ignore`.

### Task 5.3: Add coverage by test category

**Files:**
- Modify: `pytest.ini`
- Modify: `run_coverage.py`, `check_coverage.py`
- Create: `docs/quality/testing-matrix.md`

Separate unit, integration, and Home Assistant tests. Add coverage measurement and a moderate threshold only after the baseline is reproducible. Do not count skipped live tests as live evidence.

---

## Phase 6 — Documentation and CI synchronization

### Task 6.1: Update architecture documentation

**Files:**
- Modify: `docs/architecture/overview.md`, `layers.md`, `patterns.md`, `data-flow.md`
- Create: `docs/architecture/decisions/ADR-0001-clean-architecture-boundaries.md`
- Modify: `docs/developer-guide/code-organization.md`, `dependency-injection.md`, `testing.md`

Document actual dependencies and composition, not intended architecture.

### Task 6.2: Update developer bootstrap documentation

**Files:**
- Modify: `README.md`, `AGENT_SETUP.md`, `docs/developer-guide/local-development.md`, `docs/developer-guide/setup.md`

Use `.venv`, canonical commands, actual source paths, dependency installation, Home Assistant test setup, and known live-test requirements.

### Task 6.3: Repair CI workflow

**Files:**
- Modify: `.github/workflows/validate.yml`

Install the declared dependencies, use `.venv/bin/python` or an activated project environment, run collection, unit/integration/HA tests, compile, architecture checks, lint, type checking, coverage, and `git diff --check`. Keep live credentials/tests opt-in and secret-safe.

---

## Phase 7 — Final verification and review

Run, in order:

```bash
.venv/bin/python -m compileall -q cli custom_components
.venv/bin/python scripts/check_architecture.py
.venv/bin/python -m pytest cli/tests -q
.venv/bin/python -m pytest custom_components/my_verisure/core/tests -q
.venv/bin/python -m pytest custom_components/my_verisure/tests -q
.venv/bin/python -m pytest -q
.venv/bin/python -m flake8 cli custom_components
.venv/bin/python -m mypy cli custom_components
.venv/bin/python -m coverage report
 git diff --check
 git status --short --branch
```

If a check remains blocked by an unavailable Home Assistant runtime, record the exact dependency and command instead of claiming completion. Review the complete diff for architecture regressions, secret leakage, generated files, stale imports, duplicate implementations, and public contract changes.

## Completion criteria

- Canonical setup and runners work from a clean checkout.
- Test collection has no import errors.
- Application/domain code has no outward framework/vendor dependencies.
- HA and CLI adapters delegate through explicit ports/use cases.
- Auth/session/API/filesystem effects are injected and testable.
- Broken CLI contracts are corrected with regression tests.
- Architecture, lint, type, coverage, compile, and test gates are reproducible.
- CI runs the same canonical gates.
- Documentation matches the final tree.
- No credentials, tokens, private data, generated caches, or unrelated files are added.

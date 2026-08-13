# Complete pending quality plan — 2026-08-13

## Objective

Finish the remaining verified quality work in `my_verisure` without trading
architectural integrity for metric improvements. The plan is deliberately staged:
contract boundaries first, dependency cleanup second, concurrent entry isolation
third, and broad coverage/gates last.

## Verified baseline

- Branch: `master`; repository clean and aligned with `origin/master`.
- Full suite: `449 passed, 2 skipped`.
- Repowise hotspot health: `4.31`.
- Repowise worst hotspot: `core/api/alarm_client.py`.
- Source coverage from `make ci`: `82%`.
- `Coordinator` refactor already published in four slices.
- No productive `get_*_manager()` global accessor calls found by the initial
  audit; historical fallback tests/comments remain and require classification.
- Docker-based disposable HA validation is unavailable because the active user
  cannot access `/var/run/docker.sock`; no host permissions will be changed.
- No real Verisure credentials, sessions, OTPs, or provider calls are allowed.

## Workstreams

### 1. AlarmClient contract reduction

- Inventory every public/private method and classify transport, GraphQL,
  response interpretation, and polling responsibilities.
- Preserve the existing separation between initial response interpretation and
  `AlarmCommandPoller`.
- Extract only cohesive request/response policies where the contract is
  observable and independent of HA.
- Add synthetic no-network tests for success, GraphQL errors, unknown payloads,
  empty responses, transport errors, polling exhaustion, and entry-scoped
  sessions.
- Keep public result and exception contracts unchanged.

### 2. Dependency and fallback audit

- Inspect `DeviceManager`, `LogManager`, `ConfigManager`, repositories, and
  clients for global state or optional manager fallbacks.
- Replace a fallback only when the composition root already provides the
  dependency and tests prove entry isolation.
- Do not remove compatibility code mechanically; classify each occurrence as
  productive, test-only, documentation-only, or required boundary behavior.
- Add an architecture guard assertion for forbidden productive global manager
  access if the repository conventions support it.

### 3. Concurrent ConfigEntry isolation

- Build two independent composition roots with distinct credentials,
  session files, project roots, file managers, and clients.
- Exercise concurrent session refresh/cache writes with synthetic providers.
- Verify no credentials, snapshots, images, or session state cross entries.
- Verify unload and re-authentication dispose/rebuild only the selected entry.
- Keep all tests offline and deterministic.

### 4. Coverage and typing quality

- Increase coverage in high-risk production paths rather than adding tests for
  trivial lines solely to improve the percentage.
- Prioritize `AlarmClient`, `AuthClient`, `DeviceManager`, repositories,
  coordinator boundaries, services, and HA adapters.
- Resolve legitimate typing issues with precise protocols/DTO types; no broad
  `Any`, indiscriminate casts, ignores, or exclusions.
- Keep the documented `config_flow.py` `type: ignore[call-arg]` exception only.

### 5. Final gates and documentation

- Run focused tests after each slice and publish commits frequently.
- Finish with `make ci`, `make test-ha-2026-8`, compileall, architecture guard,
  pip check, diff check, Repowise, and clean-tree verification.
- Update this plan with measured results and explicit unresolved limitations.
- Do not claim manual HA or real-provider validation.

## Execution result

The pending-quality plan was executed in multiple published slices:

- `6f8a37a refactor: isolate alarm graphql request policy`
  - Added `AlarmGraphQLRequestPolicy` and `AlarmGraphQLRequest`.
  - Centralized six GraphQL operation/query/variable definitions while keeping
    transport, response interpretation, and polling separate.
- `c7f5e4e fix: preserve alarm repository result contracts`
  - `AlarmRepositoryImpl` now preserves typed `ArmResult` and `DisarmResult`
    from the client instead of using truthiness and replacing failure messages.
- `c93b75e test: prove concurrent entry isolation`
  - Added real concurrent offline persistence checks for two independent
    composition roots, sessions, configuration files, and logs.
- `1ea6bf9 guard: forbid global manager access`
  - Architecture guard now rejects productive calls to global manager accessors
    while allowing tests and documented local fallbacks.
- `0712440 test: cover alarm client edge contracts`
  - Added no-network coverage for missing authentication, incomplete CheckAlarm
    payloads, transport failures, and failed command results.

Evidence:

- `make ci`: 457 passed, 2 skipped; coverage 82%.
- `make test-ha-2026-8`: 457 passed, 2 skipped on Home Assistant Core 2026.8.1
  / Python 3.14.4.
- Focused AlarmClient/repository/request tests and composition isolation tests
  passed.
- Mypy: no issues in 209 source files.
- Critical Flake8: passed.
- `compileall`: passed.
- `ARCHITECTURE_GUARD_OK`.
- `pip check`: no broken requirements.
- `git diff --check`: passed.
- Repowise hotspot health: `4.31 → 4.36`.
- Full suite growth: `449 → 457` passed tests.

The audit found no productive global `get_*_manager()` accessor calls remaining;
manager and repository constructors are entry-scoped in the production graph.
The remaining `_resolve_file_manager()` methods are invariant boundaries, not
fallbacks to global state.

Remaining work is intentionally recorded rather than hidden: `AlarmClient` is
still the worst Repowise hotspot and its status/configuration methods remain
large adapter code. Further reduction should wait for additional explicit
contracts around provider status payloads, rather than introducing wrapper-only
abstractions. Manual Docker HA validation remains blocked by host socket
permissions, and no real Verisure validation was attempted.

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

## Acceptance criteria

- All current tests remain green; no real network/provider calls.
- Entry isolation is proven by concurrent tests, not only by constructor mocks.
- No productive global manager access remains unless explicitly justified and
  documented as an external boundary.
- AlarmClient complexity is reduced through real cohesive boundaries, not
  wrapper-only extraction.
- All quality gates pass and `master == origin/master` with a clean tree.

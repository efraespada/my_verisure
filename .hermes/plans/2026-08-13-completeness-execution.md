# Completeness execution plan — my_verisure

Date: 2026-08-13
Repository: `efraespada/my_verisure`
Target: Home Assistant Core 2026.8.1

## Objective

Move the integration from functionally validated to practically complete without
cosmetic extraction, legacy compatibility shims, or unverifiable claims. Every
slice must preserve provider and Home Assistant contracts, use entry-scoped
dependencies, add executable tests, and be committed/pushed independently.

## Baseline

- HEAD: `9a15806`
- Branch: `master`
- Working tree: clean
- Full suite: `471 passed, 2 skipped`
- Repowise hotspot health: `4.47`
- Maintainability average: `9.30`
- Worst hotspot: `core/api/auth_client.py`, score `1.0`, NLOC `576`, CCN `15`
- Other major hotspots: `camera_client.py` NLOC `422`, CCN `38`; coordinator
  NLOC `441`; alarm_client now NLOC `475` in Repowise.
- No real Verisure calls have been made.
- Docker-based isolated HA validation is currently blocked by Docker socket
  permissions and must not be bypassed by changing host permissions.

## Execution slices

### Slice 0 — baseline and plan

Record current metrics, complete the plan, and keep the repository clean before
changes.

### Slice 1 — remove contradictory legacy documentation and implicit fallbacks

- Update documentation that still describes the global session accessor as the
  active architecture.
- Inventory optional manager dependencies and distinguish legitimate test/CLI
  compatibility from product runtime behavior.
- Remove a fallback only when all production composition paths and tests prove
  the dependency is available explicitly.
- Strengthen architecture guards for forbidden production fallbacks and stale
  imports.
- Add entry-scoped construction and concurrent isolation regressions where
  needed.

### Slice 2 — AuthClient

Extract only cohesive boundaries such as request construction, authentication
response classification, and session persistence coordination. Preserve login,
OTP, reauthentication, invalid credentials, transport errors, GraphQL errors,
and session-expiry semantics. Add contract tests before deleting inline logic.

Execution started in `2a8c23f`:

- `AuthSessionPersistence` owns session projection and entry-scoped credential
  persistence for normal and post-OTP login.
- 18 authentication/session contract tests pass.
- AuthClient reduced from 703 to 680 lines.
- Full mypy covers 217 files without errors.

### Slice 3 — CameraClient and InstallationClient

Audit each separately. Extract request/response policies only where they have
independent observable contracts. Increase coverage for partial responses,
missing installations/devices, image selection/storage failures, and transport
errors. Do not create generic adapters merely to reduce NLOC.

Execution:

- `b986a12`: `CameraResponseInterpreter` isolates initial request and polling
  status interpretation. CameraClient reduced from 508 to 444 lines.
- Current installation slice adds `InstallationResponseInterpreter` for
  installations, services, and devices. InstallationClient reduced from 382 to
  334 lines.
- 16 camera tests and 19 installation/interpreter tests pass in focused gates.
- Mypy covers 221 files without errors.

### Slice 4 — Coordinator lifecycle

Characterize and test refresh, reauthentication, failure recovery, unload,
cancellation, and entry isolation. Keep HA exception mapping at the integration
boundary and application policies independently testable.

Execution:

- Coordinator now passes `config_entry=entry` explicitly to HA Core 2026.8.1,
  avoiding implicit ContextVar entry resolution.
- `async_cleanup()` calls HA's `async_shutdown()` and clears registered entity
  references.
- `async_unload_entry()` invokes cleanup and clears `runtime_data` after platform
  unload.
- Focused HA lifecycle/reauth/composition suite: 11 passed.


### Slice 5 — HA-facing adapters

Increase tests for alarm control panel, sensor, binary sensor, button, services,
diagnostics, config flow, reauth, and lifecycle. Validate states, attributes,
availability, registration/removal, and actionable error reporting against HA
2026.8.1 contracts.

Execution:

- Added diagnostics redaction/session-summary coverage.
- Fixed camera refresh button to clear its busy state in `finally` after both
  success and failure.
- Added success/failure button lifecycle tests.
- Focused adapter suite: 13 passed; previous HA lifecycle suite remains green.
- Mypy covers 222 files without errors.

### Slice 6 — integration limitations

Attempt isolated HA validation only if Docker becomes available without host
permission changes. Do not use real credentials or provider sessions. If the
provider sandbox/isolated HA path is unavailable, record the exact blocker and
separate synthetic contract evidence from live evidence.

Execution:

- `docker info` confirms Docker Engine 29.6.2 is installed, but the current
  user receives `permission denied` for `/var/run/docker.sock`. No host
  permissions were changed.
- No Verisure credentials, OTP, real session, or provider call was used.
- HA Core 2026.8.1 tests and synthetic contracts are the available evidence;
  isolated Docker and provider E2E remain explicitly unverified.
- The only `importorskip("homeassistant")` is in a smoke-import guard; the
  actual HA gate runs with the pinned HA environment and passes all tests.

### Slice 7 — final gates and release evidence

Run full HA suite, mypy, critical/full lint as appropriate, compileall,
architecture guard, pip check, diff check, coverage, Repowise, and git
verification. Update this plan with measured before/after results, remaining
limits, commits, and exact evidence. Push every validated slice and finish with
`HEAD == origin/master` and a clean tree.

Execution:

- Published slices: `12b4c64`, `2a8c23f`, `7faf19d`, `b986a12`, `ff53ace`,
  `4a6ad59`, `d2a0425`.
- `make test-ha-2026-8`: **494 passed** on HA Core 2026.8.1/Python 3.14.4.
- `make ci`: passed full tests, mypy (222 files), critical lint, compileall,
  architecture guard, pip check, diff check, and coverage.
- Official Makefile coverage: **84%** over 9,108 statements.
- Repowise: hotspot health **4.60**, maintainability average **9.34**;
  worst hotspot remains `AuthClient` (score 1.0, max CCN 14, NLOC 539).
- Final verification: `HEAD == origin/master`, clean tree, generated coverage
  artifacts removed.

## Follow-up completeness plan — 2026-08-13

The previous execution established a green HA Core 2026.8.1 baseline. The
remaining work is deliberately split by risk rather than by raw coverage:

1. **HA service contracts:** exercise every registered handler, unknown-entry
   behavior, refresh failures, dispatcher failures, service cleanup, and schema
   rejection. Replace only broad catches whose failure contract can be made
   explicit; retain isolation at the HA boundary where one service failure must
   not crash Home Assistant.

Execution:

- Added `test_services_contracts.py` covering all four alarm handlers, entry
  matching, status refresh, camera refresh cleanup, dispatcher failures, and
  schema rejection.
- Focused service/adapter suite: **15 passed**.
- Mypy and critical lint remain green across 223 files.
2. **Alarm platform lifecycle:** verify arm/disarm transition state on success,
   failure, missing installation IDs, unavailable coordinator data, entity
   registration, and removal. Fix any state that can remain stuck after a
   completed command.

Execution:

- Added lifecycle tests for successful arm/disarm, service failure, missing
  installation ID, and coordinator availability.
- Cleared alarm transition state after successful completion for all four command
  paths; failure paths already clear it as well.
- Focused platform suite: **24 passed**.
- Mypy covers 224 files without errors.
3. **Critical client contracts:** cover installation/auth/device-manager paths
   for empty payloads, malformed payloads, authentication expiry, transport
   errors, and safe exception conversion. Do not extract code without a cohesive
   contract.

Execution:

- Added required-identifier validation to `DeviceManager` for persisted device
  data. Partial/corrupt files now regenerate entry-scoped identifiers instead of
  failing later with `KeyError` during login or OTP.
- Added regression coverage for partial persisted identifiers and preserved
  entry isolation.
- Focused client suite: **21 passed**.
- Mypy covers 224 files without errors.
4. **Live-boundary evidence:** retry only read-only environment discovery for
   Docker/HA availability; never change host permissions or use provider
   credentials. Record blockers precisely.

Execution:

- Docker Engine 29.6.2 is installed, but `docker info` still returns
  `permission denied` for `/var/run/docker.sock` for the current user.
- HA Core checkout remains available at `/tmp/ha-core-2026.8.1` with Python
  3.14.4; no Docker permissions were changed.
- No Verisure credentials, OTP, real session, or provider request was used.
- Isolated Docker HA and provider E2E remain explicitly unverified.
5. **Final gates:** run the official Makefile suite, HA Core suite, type/lint/
   architecture/compile/dependency checks, official coverage, Repowise, and
   branch cleanliness. Publish each validated slice independently.

Execution:

- `make ci`: passed.
- `make test-ha-2026-8`: **505 passed** on HA Core 2026.8.1/Python 3.14.4.
- Mypy: **224 source files**, no errors.
- Critical lint, compileall, architecture guard, pip check, and diff check:
  all passed.
- Official Makefile coverage: **85%** over 9,243 statements.
- Repowise: hotspot health **4.59**, maintainability average **9.34**; worst
  hotspot remains `AuthClient` with score 1.0.
- Published slices: `b257e49` (service contracts), `ff66296` (alarm panel
  lifecycle), and `ce5dc50` (device identifier validation).
- Final branch verification and generated-artifact cleanup remain required
  immediately before the documentation commit.

## Definition of done

- No contradictory active legacy documentation.
- No unintentional global manager access or product fallback.
- AuthClient, CameraClient, InstallationClient, and Coordinator boundaries are
  contract-driven and tested.
- Entry-scoped concurrency, reauth, unload, and cancellation are tested.
- HA-facing behavior has focused tests for all supported platforms/services.
- All skips are documented and justified.
- Full gates pass, metrics are measured, and live-validation limits are explicit.

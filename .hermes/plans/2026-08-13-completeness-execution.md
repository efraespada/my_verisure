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

### Slice 3 — CameraClient and InstallationClient

Audit each separately. Extract request/response policies only where they have
independent observable contracts. Increase coverage for partial responses,
missing installations/devices, image selection/storage failures, and transport
errors. Do not create generic adapters merely to reduce NLOC.

### Slice 4 — Coordinator lifecycle

Characterize and test refresh, reauthentication, failure recovery, unload,
concurrent refresh, and cancellation. Separate remaining application policies
from HA lifecycle glue. Prove that one ConfigEntry cannot affect another and
that no orphan asyncio tasks remain after unload.

### Slice 5 — HA-facing adapters

Increase tests for alarm control panel, sensor, binary sensor, button, services,
diagnostics, config flow, reauth, and lifecycle. Validate states, attributes,
availability, registration/removal, and actionable error reporting against HA
2026.8.1 contracts.

### Slice 6 — integration limitations

Attempt isolated HA validation only if Docker becomes available without host
permission changes. Do not use real credentials or provider sessions. If the
provider sandbox/isolated HA path is unavailable, record the exact blocker and
separate synthetic contract evidence from live evidence.

### Slice 7 — final gates and release evidence

Run full HA suite, mypy, critical/full lint as appropriate, compileall,
architecture guard, pip check, diff check, coverage, Repowise, and git
verification. Update this plan with measured before/after results, remaining
limits, commits, and exact evidence. Push every validated slice and finish with
`HEAD == origin/master` and a clean tree.

## Definition of done

- No contradictory active legacy documentation.
- No unintentional global manager access or product fallback.
- AuthClient, CameraClient, InstallationClient, and Coordinator boundaries are
  contract-driven and tested.
- Entry-scoped concurrency, reauth, unload, and cancellation are tested.
- HA-facing behavior has focused tests for all supported platforms/services.
- All skips are documented and justified.
- Full gates pass, metrics are measured, and live-validation limits are explicit.

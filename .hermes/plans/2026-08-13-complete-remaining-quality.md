# Complete remaining work plan — 2026-08-13

## Scope

Close the remaining quality work for `my_verisure` without claiming provider or
household end-to-end validation that has not been run. Runtime target remains HA
Core 2026.8.1 with Python 3.14.4. Every code slice requires characterization or
regression tests, focused gates, a commit, and a push.

## Workstreams

### A. Isolated Home Assistant validation

- Use the installed HA Core checkout and pytest harness as the deterministic
  lifecycle gate.
- Attempt a disposable HA Core process only if the environment supports it;
  never use household HA, real credentials, or real Verisure calls.
- Validate imports, config flow, setup/reload/unload, two-entry isolation,
  service/entity cleanup, diagnostics redaction, and packaging.
- Record exact blockers rather than replacing unavailable manual evidence with a
  fabricated success.

### B. Structural hotspots

- Re-audit Coordinator and AlarmClient after the previous extractions.
- Characterize remaining public/error boundaries first.
- Extract only cohesive application responsibilities (protocol response mapping,
  persistence orchestration, or state transitions), not wrappers or cosmetic
  line splitting.
- Preserve entry-scoped composition and all public result contracts.

### C. Quality debt

- Search all production code for type ignores, global/singleton fallbacks,
  unsupported legacy HA references, broad exception handling, and secret-bearing
  logging.
- Replace only justified debt. Dynamic HA/Injector boundaries must remain
  localized and documented if unavoidable.
- Verify CI, Makefile, dependency declarations, `pip check`, architecture guard,
  compileall, and Repowise consistency.
- Do not refactor tests merely to improve Repowise duplication metrics.

### D. Final release gate

- Run full HA-targeted suite, contextual coverage, mypy, lint, architecture,
  dependency, import, diff, and artifact checks.
- Re-run Repowise and classify residual findings.
- Update documentation with exact evidence and limitations.
- Ensure `master == origin/master` and a clean tree.

## Acceptance criteria

- No known regression; all focused and full tests pass.
- No new unsupported compatibility shim, global state, unbounded `Any`, or secret
  exposure.
- Structural changes have tests proving behavior and isolation.
- Manual/Docker/provider limitations are explicit and not misreported as passed.
- All changes are committed and pushed in small verified slices.

## Iteration result

Completed slices:

- removed the root CLI `sys.path` mutation and extended the architecture guard;
- pinned CI to Python 3.14.4;
- consolidated duplicated alarm GraphQL transport preparation while preserving
  AlarmClient result contracts;
- covered ConfigFlow options and the real HA reauth lifecycle;
- documented the one unavoidable HA `ConfigFlow.__init_subclass__` typing
  boundary.

Measured evidence: 394 passed, 2 skipped, 78% total coverage. Repowise reports
AlarmClient duplication reduced from 42.94% to 33.54%; CameraClient duplication
is 2.68%. Coordinator remains the primary structural hotspot and is explicitly
deferred for a separate characterization-led iteration rather than a risky
large rewrite.

Manual Docker validation remains blocked: Docker is installed, but the current
operator lacks permission to access `/var/run/docker.sock`. No household HA or
real Verisure account was used.

## Follow-up iteration — Coordinator and composition scope

Additional completed slices:

- extracted `CoordinatorSnapshotStore` as an entry-scoped application boundary;
- moved coordinator snapshot load, save, and metadata operations behind that
  boundary while preserving the public coordinator helpers;
- removed implicit `FileManager` and `SessionManager` construction from
  `MyVerisureModule`; the composition factory now owns explicit construction;
- added regression tests for snapshot persistence and dependency-module scope.

Updated evidence: 400 passed, 2 skipped, 79% total coverage. Coordinator is now
597 NLOC and 34% covered. The remaining coordinator responsibilities are
authentication policy, provider refresh error mapping, alarm commands, camera
refresh orchestration, notifications, and translation loading; those require
separate characterization-led slices and were not bundled into this iteration.

## Follow-up iteration — Coordinator, protocol boundaries, cameras, and HA adapters

Completed additional quality slices:

- isolated the coordinator authentication decision (authenticated session,
  cached snapshot, or no usable data) behind an application policy;
- isolated realtime alarm GraphQL response interpretation (`OK`, `KO`, `WAIT`,
  unknown, and GraphQL errors) without moving transport or retry timing;
- centralized active Verisure camera selection and identifier formatting for the
  refresh and dummy-image use cases;
- removed redundant exception wrappers from the installation use case so
  repository exceptions propagate without artificial rethrow layers;
- added HA camera adapter coverage for missing directories, invalid timestamp
  directories, preferred thumbnails, and fallback image files.

Focused evidence for these slices: 8 coordinator tests, 15 alarm tests, 7
camera use-case tests, 6 installation-use-case tests, and 26 HA adapter/lifecycle
tests passed. Mypy and critical Flake8 passed after each slice. Each slice was
committed and pushed independently.

The remaining coordinator responsibilities (provider refresh error mapping,
alarm command orchestration, notifications, and translation loading) remain
separate candidates for future characterization-led slices. 
## Follow-up iteration — Coordinator and client hotspot reduction

Completed independently verified slices:

- `AlarmClient`: isolated initial arm/disarm GraphQL response interpretation in
  `AlarmCommandResponseInterpreter`; transport and polling remain separate.
- `Coordinator`: isolated provider failure classification and retained HA-only
  notification/cache/auth side effects at the adapter boundary.
- `AuthClient`: isolated OTP metadata validation and phone selection without
  mutating provider response dictionaries.
- `CameraClient`: isolated request context/header construction and image
  timestamp-directory normalization.
- `Coordinator`: consolidated four alarm command adapters into one typed command
  executor driven by explicit command metadata, removing duplicated notification
  and error handling without replacing the existing application dispatcher.

Focused evidence: 13 alarm tests, 16 coordinator failure tests, 15 authentication
 tests, 15 camera tests, and 24 coordinator command/service tests passed across
 the slices. Full HA-targeted validation then passed with 431 tests and 2 skips;
 total coverage reached 81%. Mypy passed on 196 source files, critical Flake8,
 compileall, architecture guard, pip check, and git diff checks passed.

Repowise advisory evidence improved from hotspot health 4.13 to 4.28,
average health 8.87 to 8.91, and maintainability average 9.20 to 9.24. The
Coordinator remains the worst structural hotspot, and AlarmClient/AuthClient/
CameraClient remain substantial files; this iteration reduced concrete
responsibility duplication but did not claim that all monoliths are eliminated.
Manual HA Docker validation and real Verisure validation remain unavailable and
were not substituted with fabricated evidence.

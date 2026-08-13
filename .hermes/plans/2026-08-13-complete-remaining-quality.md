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

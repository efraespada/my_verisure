# Repository quality audit — 2026-11-23

This audit started from `develop` at `d6b14df` and includes the corrections on
`feature/project-quality-audit`. The supported target is **Home Assistant
2026.11.2**, with its matching official `pytest-homeassistant` harness. Earlier
version receipts are historical evidence; their requirements, runner and active
support have been retired at the owner's request.

The review covered production core, HA adapters, CLI, test quality, dependency
declarations, persistence, cancellation, documentation, examples and packaging.
All integration tests used synthetic data and temporary storage. This audit sent
**zero provider requests and zero physical alarm commands**. Public dependency
metadata and GitHub checks were queried separately.

## Reproduced defects and corrections

| Priority | Defect | Correction and regression evidence |
|---|---|---|
| P1 | Each periodic snapshot repeated detailed installation discovery while preparing local placeholders, adding three cloud calls per cycle. | Reuse snapshot camera identifiers; a complete coordinator pipeline test asserts one detailed read. Placeholders use a local adapter and cannot invalidate a good state snapshot. |
| P1 | Negative intervals could schedule continuous polling; zero could disable the polling fallback. | Shared exact-integer policy accepts 1–1440 minutes; invalid saved values recover to ten minutes. Both options validation and actual coordinator initialization are exercised. |
| P1 | A replacement password could be accepted by renewing with the old session's refresh token. | Refresh requires matching user and password. Changed credentials use provider password login; rejection preserves prior memory and disk. |
| P1 | Valid JSON with an invalid session shape/type could repeatedly break authentication recovery. | Validate the complete persisted session before mutating memory; malformed data permits a clean login with configured credentials. |
| P1 | Empty, invalid, non-image or truncated base64 content could be committed as a photo. | Strict base64, byte/pixel limits, container preflight, format restriction, image verification and decoding precede publication. Failure cannot emit `photo_ready`. |
| P1 | Duplicate photo IDs counted overwritten files as separate successful images; a failed rewrite could retain an older completion marker. | Validate distinct safe filenames before writing, invalidate the previous marker, and mark complete only after every expected image is persisted. |
| P1 | An unchecked image container could invoke unnecessary metadata/animation decoders before image-size checks. | Bound JPEG/PNG framing and geometry before Pillow; remove unnecessary metadata, reject animation and verify/persist sanitized bytes. Pixel-preservation and early-rejection tests use tiny synthetic images. |
| P2 | Invalid/nonfinite JWT expiration could appear unexpired; missing decoding support failed open. | Bound ASCII metadata to 64 KiB; require a JSON object and finite numeric expiry; fail closed on malformed values. Unsigned metadata never authenticates a user. Missing `exp` retains the independent session TTL. |
| P2 | `get_status` returned success for missing installations or failed coordinator refreshes. | Raise a sanitized HA error, including when the coordinator records failure without raising. |
| P2 | Some CLI tests mocked the method they claimed to test; tests could resolve the operator's normal state directory. | Exercise real handlers through synthetic ports and isolate CLI state under each test's temporary directory. |
| P2 | CLI batch commands could request input or skip explicit confirmation, and failed camera captures could return success. | Propagate noninteractive policy, require `--no-confirm` for batch alarm writes, reject ambiguous installation selection without prompting, and propagate camera failure exit status. |
| P2 | A tracked runtime device artifact exposed account/device identity in its filename/content. | Remove the unused artifact, ignore per-user device files and add a privacy regression. Historical Git objects are not rewritten; removal is not revocation. |
| P2 | An example automation could disarm for unknown values; freshness examples used the wrong timestamp or failed rendering. | Require explicit `disarmed`, use the actual update timestamp, and validate HA schemas/template rendering with the real engine. No example automation was activated. |
| P2 | The CLI test runner concealed failures; development commands used inconsistent interpreters. | One canonical Make gate, preserved exit status, current pinned setup and isolated tooling regressions. Docker stops retain configuration. |
| P3 | `ConfigManager` wrote an envelope but read it as a flat configuration; shallow defaults leaked mutations. | Support the stored envelope and legacy flat data; return independent nested defaults. Real temporary-file round trips exercise the contract. This manager had no active HA caller. |

Representative tests are listed in the [machine-readable receipt](../validation/2026-11-23-project-quality-audit.json)
and [capability catalog](../../specs/catalog.json). Regressions were observed
failing before their corresponding corrections; a passing mock alone was not
treated as a reproducer.

## Architecture assessment

The core has no HA imports. Domain values/policies and use cases depend on
semantic ports, with provider clients, persistence and Pillow in adapters.
Snapshot projection stays pure; JSON/stat operations moved to
`core/coordinator_snapshot_store.py`. The alarm dispatcher receives an installation
ID rather than the HA config-entry shape. Entry-owned composition and intentional
shared provider/installation admission remain separate.

The [AST guard](../../scripts/architecture_guard.py) checks absolute and relative
imports across all core production files, including new models. Its regressions
cover import forms that the earlier substring checks missed. See
[ADR 0001](../adr/0001-core-and-adapter-dependencies.md) and
[project context](../../CONTEXT.md).

This establishes executable dependency direction, not a claim that every module
has ideal size. The coordinator/config flow remain large. HTTP adapters still
create a session per request; connection reuse is a performance opportunity,
without a demonstrated remaining correctness defect. Removing useful ports or
adding an interface for each OS/library call would not improve this design.

## Testing and verification

The [quality status](../quality-status.md) and receipt contain the final counts,
coverage denominators, context count and commands. The measurement excludes test
code and separates integration, CLI and tools; it must not be presented as 100%
global coverage. `make coverage` rejects missing production files in those scopes,
line/branch regressions and uncovered paths in the ten notification modules plus
six critical image/placeholder/polling/JWT modules.

Coverage uses the C tracer because the current sys.monitoring tracer cannot
record the requested per-test dynamic contexts. Runtime and unraisable coroutine
warnings fail tests. The type gate uses the repository's existing mypy settings,
including `--ignore-missing-imports`; it is not a strict-typing certification.

Config-flow recovery, coordinator failure paths and broader CLI scenarios remain
the main coverage gaps. Increasing the percentage with tests that only assert
their own mocks would not close those gaps. The complete Flake8 baseline still
contains style findings; the blocking `E9,F` gate is clean and includes unused
imports/variables. Full lint is not reported as passing.

## Current runtime dependency security

Home Assistant 2026.11.2 is the current stable target and supplies the tested
aiohttp 3.14.5, PyJWT 2.15.1, cryptography 50.0.2 and Pillow 13.0.0 versions.
The manifest/CLI minimums now match those verified versions, with Probatio for
HA forms/actions. `cryptography` and `http-ece` are direct declared dependencies
because production imports them. [Official Core dependency pins](https://github.com/home-assistant/core/blob/2026.11.2/pyproject.toml).

The isolated `pip-audit` scan covers the installed default dependency closure of
the integration's manifest, exported without credentials, paths or household
metadata. Its final result is in the receipt. It does not audit every optional
Home Assistant integration or prove absence of unpublished vulnerabilities.
CI repeats this audit without installing the audit tool into the HA environment.

Small, bounded image regressions confirmed the relevance of the upstream EXIF
and early-animation-allocation corrections; current Pillow includes those fixes.
The framing sanitizer is additional defense and does not replace dependency
updates. [Pillow EXIF advisory](https://github.com/python-pillow/Pillow/security/advisories/GHSA-wqgw-9xfh-qf2g),
[Pillow APNG advisory](https://github.com/python-pillow/Pillow/security/advisories/GHSA-5xm2-6676-qcp9).

No open GitHub secret-scanning alert was returned during review. Dependabot alerts
were disabled and its API lacked the required administrative scope; that API is
not evidence of a clean dependency graph. The independent scan and CI gate supply
the recorded dependency check. Existing historical account/device data may remain
in Git history, clones or forks; no history rewrite or live device revocation was
performed.

## Documentation and operational limits

README, setup, architecture, DI, authentication, event/service references,
contribution guidance and SDDs now describe the current implementation. Local
file links and catalog paths have an offline gate. Actual HA schemas, templates,
notification-guide examples and blueprint expansion have executable checks.
Anchors and remote links are outside the link guard's scope.

Docker/Dev Container paths received static and synthetic tooling checks; no
container was started. This audit did not reinstall the changed source on the
household instance or repeat physical alarm/camera tests. Prior
[live receipts](../validation/2026-11-23-notification-implementation.json) describe
their own installed build. Total/away testing remains reserved for the owner,
and broader non-photo delivery, camera-family parity and freshness UX remain
evidence limits. No audit can turn these untested cases into verified behavior.

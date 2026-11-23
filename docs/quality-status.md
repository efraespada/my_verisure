# Quality status

Updated: 2026-11-23. Current supported target: **Home Assistant Core 2026.11.2**.

## Verified local evidence

- Python `3.14.6`; official harness `pytest-homeassistant==2026.11.2`.
- Complete suite: **1,704 passed, zero failures and warnings**.
- Mypy: no issues in **326 source files** with the repository's existing settings.
- Blocking Flake8 `E9,F`: passing; full style lint remains a separate, failing baseline.
- Architecture, documentation, dependency consistency and distribution gates are
  required by `make ci`; PR results are reported by GitHub separately.
- Isolated `pip-audit`: **zero known advisories across 19 installed dependencies**
  in the integration's declared default runtime closure. This excludes unrelated
  optional HA integrations and is a dated scan, not a future security guarantee.

| Measured scope | Executable lines | Branches | Missing lines / branches |
|---|---:|---:|---:|
| HA integration/core | **85.21%** (8,123 / 9,533) | **76.00%** (1,818 / 2,392) | 1,410 / 574 |
| CLI | **73.40%** (643 / 876) | **60.07%** (167 / 278) | 233 / 111 |
| Quality tools | **77.84%** (267 / 343) | **69.28%** (115 / 166) | 76 / 51 |

The denominator excludes tests and third-party packages. These three scopes do
not include the thin root CLI launcher. **Global coverage is incomplete.**
Config-flow/coordinator recovery and broader CLI behavior are the principal gaps.

CI enforces line/branch floors of 85/76 for integration, 73/60 for CLI and 77/69
for tools, rejecting omitted source files. Ten notification modules and six
additional image/placeholder/polling/JWT modules require **100% executable lines
and branches**. See their exact lists in
[`check_notification_coverage.py`](../scripts/check_notification_coverage.py) and
[`check_project_coverage.py`](../scripts/check_project_coverage.py).
The C tracer recorded **1,913 per-test contexts**; sys.monitoring is not used
because it cannot supply the requested dynamic contexts in this tool version.

The [repository audit](technical/2026-11-23-project-quality-audit.md) explains the
reproduced defects, fixes, architecture decisions, privacy review and limitations.
The [machine-readable receipt](validation/2026-11-23-project-quality-audit.json)
records exact versions, denominators and regression paths.

## Architecture and documentation

Policies/models/use cases do not import HA or concrete provider/storage/image
adapters. Absolute and relative imports are checked across the core with AST
regressions. Snapshot projection remains pure; local image/persistence adapters
implement semantic ports. The [decision](adr/0001-core-and-adapter-dependencies.md)
and [project context](../CONTEXT.md) describe ownership and domain invariants.
The coordinator and config flow remain large; reusable HTTP sessions are a
performance opportunity, without a remaining reproduced correctness defect.

README, developer/user/API guides and [SDDs](../specs/README.md) describe the
current target. Local Markdown destinations/catalog references have an offline
gate. Actual HA schema/template tests validate examples and blueprint expansion.
Anchors and remote links are not included in the link checker.

The full Flake8 report contains historical line-length/whitespace and other style
findings. They are not hidden behind a global ignore. The blocking gate includes
all Pyflakes findings, including unused imports/variables, plus syntax errors.
Mypy allows untyped code and missing third-party stubs; passing is not strict
coverage of every type or runtime path.

## Deployment and physical evidence

This audit ran offline against HA 2026.11.2 packages and did **not** reinstall its
changed source on the household host, start Docker or send alarm/camera requests.
The native harness uses per-test temporary HA configuration; CLI tests use private
temporary state. Total/away tests remain reserved for the owner.

The earlier [notification implementation receipt](validation/2026-11-23-notification-implementation.json)
records the installed build's selected-camera delivery, correlated `photo_ready`,
restart/reload identity preservation and measured timing. Earlier
[alarm/camera live evidence](validation/2026-11-22-live-verisure.md) and
[push evidence](validation/2026-11-23-ha-push.json) remain historical observations.
They do not establish physical behavior for every subsequent source change.
General non-photo delivery, broader camera-family parity and freshness UX still
need separate evidence.

No open secret-scanning alerts were returned during this review. The accidentally
tracked runtime device artifact was removed and guarded; its historical Git
objects were not rewritten. Dependabot alerts are disabled and its administrative
API was unavailable; the independent dependency scan now runs in CI. Credentials,
OTPs, device files, raw captures and private photos must remain outside Git.

## Reproduction

```sh
python3.14 -m venv .ha-2026.11-venv
make install
make ci
```

Set `HA_PYTHON` to reuse another environment containing the exact current pins.
The [audit plan](superpowers/plans/2026-11-23-project-quality-audit.md) records the
work. Active legacy requirements/runners have been retired; historical receipts
are retained without rewriting their original measurements.

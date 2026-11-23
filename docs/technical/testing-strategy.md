# Testing strategy

The canonical commands and environment are described in
[developer testing](../developer-guide/testing.md) and `Makefile`.

## Current layers

- Domain and application tests exercise policies with synthetic ports/fakes.
- Adapter contract tests exercise DTO parsing, GraphQL request shape, persistence,
  crypto framing and provider failure classification without a provider call.
- CLI tests check command routing, input, display and injected session behavior.
- Real Home Assistant test fixtures exercise config flows, entities, options,
  services, events, restore, context, multiple entries and teardown.

The HA harness is present; it is not a substitute for a full frontend/browser
or physical-device test. Protocol source support and synthetic category tests
also do not prove delivery of every notification on a household contract.

## Coverage and regression gates

`make coverage` measures integration, CLI and validation-script production lines
and branches. It enforces per-package regression floors with
`scripts/check_project_coverage.py` and complete
executable line/branch coverage in the ten listed notification modules through
`scripts/check_notification_coverage.py`. That threshold does not apply to the
whole repository. See [quality status](../quality-status.md) for the measured
baseline and its denominator. The integration, CLI and tooling have separate denominators and floors;
those floors preserve the measured baseline rather than imply full coverage.

Add behavior regressions for concrete risks: stale reads, cancellation,
authentication rollback, shared-installation serialization, durable writes,
replay, permissions and bounded provider admission. Keep clocks deterministic,
assert observable results, and patch external effects rather than the policy
under test. No automated test should call the real provider or need credentials.

## Remaining evidence

Broader camera families, non-photo delivery, full frontend behavior and physical
compound-command recovery require separately controlled evidence. Use sanitized
fixtures and dated validation records; never commit raw captures or household
storage. [Capability baselines](../../specs/CATALOG.md) distinguish these limits
from completed synthetic regression checks.

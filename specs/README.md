# My Verisure specification standard

Specifications describe observable product contracts, their evidence and their
limits. They complement source code, tests and user documentation. They do not
authorize live alarm operations.

This structure is adapted from the public [Copilot specification standard](https://github.com/vypdev/copilot/blob/master/specs/README.md)
and [template](https://github.com/vypdev/copilot/blob/master/specs/_template.md),
inspected on 2026-11-22. Reference template blob:
`2c20640d3b9e6812ddf02cdecfe7752e5a6b09fa`.
Copilot is not installed or enabled by these documents.

## Inventory and status

[catalog.json](catalog.json) follows the inspected version-1 capability inventory
shape. [CATALOG.md](CATALOG.md) is its human-readable companion, maintained together
until specification tooling is explicitly integrated.

| Status | Meaning |
|---|---|
| Draft | A proposed contract with unresolved decisions or incomplete review |
| Ready for implementation | Maintainers have resolved decisions and reviewed acceptance, design and verification |
| As-built baseline | Evidence-backed description of existing behavior, including known defects and missing evidence |

An as-built baseline is not a claim of complete live validation. Separate observed
facts, the contract to preserve, limitations, unknown historical rationale and
proposed improvements. Catalog `as-built-baseline` entries retain that distinction.

The five baselines cover native authentication, alarm confirmation,
installation/camera identity, Linux FCM photo completion and
[notification observability/automation](notification-observability-and-automation.md).
The notification contract includes a separate source catalog, the original defect
audit and the implementation's synthetic/real-HA-platform verification. Source
support remains distinct from actual non-photo delivery on a household account.
The [quality record](../docs/quality-status.md) separates pinned offline checks from
controlled household evidence. Alarm total remains outside the live-tested scope.

## Required content

Use [_template.md](_template.md). Every specification covers its numbered sections
or explains why a concern does not apply. Requirements have stable IDs and map to
acceptance, code ownership, tests/evidence and documentation. Include:

- actors, terminology, current and intended journeys;
- complete state transitions, cancellation, partial success and recovery;
- configuration defaults, precedence, persistence and migration;
- actual Clean Architecture boundaries and executable dependency checks;
- concrete UI messages for pending, action-required, failed, partial and completed states;
- privacy, authorization, bounded retries and operational limits;
- a risk-derived numeric test budget and truthful coverage requirements;
- rollout, rollback, discovery, acceptance and remaining review decisions.

For dependent transitions, use a small diagram plus its textual equivalent.
Treat unknown provider data as unknown; a specification cannot turn an assumption
into verified behavior. Live timing evidence distinguishes backend confirmation
from an upper bound obtained by observing a screen.

## Local verification

The existing commands are `make test-ha-2026-8`, `make type-check`,
`make lint-critical`, `make git-check`, `make distribution-check` and
`make coverage`, with `HA_PYTHON` pointing at the supported environment.
Automated tests use synthetic data and no live provider.

This repository currently has no Copilot specification validator/generator.
The SDK's `validate:specifications` and `generate:specifications` commands are
not installed here. Future integration must verify its selected SDK version,
schema and ownership rules before claiming compatibility or enabling automation.
Until then, review JSON shape, unique capability IDs, existing relative paths,
links, numbered sections and the Markdown/catalog agreement locally.

## Operational evidence

Commit only sanitized contracts and outcomes. Keep passwords, SMS codes, tokens,
device identifiers, household addresses, raw HAR files and private photos outside
the repository. Record explicit authorization, permitted modes, stop conditions
and restoration in a controlled live verification report. A temporary prohibition
on alarm writes takes precedence over a pending test plan.

See [the live validation plan](../docs/superpowers/plans/2026-11-22-live-verisure-validation.md)
for this iteration's execution record.

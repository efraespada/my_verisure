# Current gaps and evidence limits

This is a current backlog summary. Earlier reauthentication, global injector,
panel identity and missing HA lifecycle findings have correction regressions;
they are not outstanding product defects. See [quality status](../quality-status.md)
and the [capability catalog](../../specs/CATALOG.md).

## Remaining evidence

- Provider delivery of non-photo notification categories and entitlement-dependent
  behavior remains unverified on the household account.
- Camera-family coverage is narrower than the provider's full product range.
- Total/away live testing remains reserved to the owner; synthetic command tests
  do not establish physical compound-command recovery in every partial failure.
- Full frontend and isolated-container lifecycle checks are distinct from the
  real HA Python harness and were not executed in the latest implementation.
- Restored/stale image presentation and broader freshness UX remain acceptance
  boundaries; a displayed historical photo is not proof of a fresh capture.

## Technical debt and maintenance

- Production coverage has gaps outside the ten fully gated notification modules.
  Assess uncovered branches by risk rather than treating a global number as proof.
- The full Flake8 baseline retains historical whitespace/line-length debt.
- Normal-operation warning traces and translation patterns merit incremental
  cleanup. Keep changes scoped and preserve safe logging.
- Keep README, current guides and capability specifications synchronized with
  executable gates; label historical receipts rather than overwriting them.

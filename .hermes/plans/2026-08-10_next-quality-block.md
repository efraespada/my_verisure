# Next Quality Block — Home Assistant Adapters and Composition Root

## Scope

Continue after commit `f6baf64` by improving runtime adapter coverage, typing, and
composition boundaries without masking the existing quality baseline.

## Execution plan

1. [x] Audit `sensor.py`, `integration.py`, `services.py`, entry points, and current
   tests; record the real lifecycle contracts.
2. [x] Add focused behavior tests for setup/unload, service registration, and the
   highest-value sensor/service branches.
3. [x] Fix production defects exposed by those tests using RED-GREEN-REFACTOR.
4. [x] Resolve the associated mypy errors at the adapter boundaries.
5. [ ] Reduce Flake8 debt in files touched by this block without broad ignores.
6. [ ] Run the complete test, compile, architecture, critical lint, incremental
   typing, coverage, and diff gates.
7. [ ] Update the architecture audit and publish a separate commit.

## Guardrails

- Do not add compatibility shims for deleted historical APIs.
- Do not write to real Home Assistant during tests.
- Keep HA objects at adapter boundaries and application ports below them.
- Do not claim full mypy/Flake8 success while their repository baselines remain.
- No commit until all applicable gates for this block pass.

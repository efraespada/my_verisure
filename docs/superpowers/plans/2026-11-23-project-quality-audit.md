# Project Quality Audit Implementation Plan

> **For agentic workers:** execute the independent architecture, runtime and documentation reviews with separate file ownership, then review and verify the combined result.

**Goal:** Audit the entire repository, correct reproduced defects and make architecture, testing and documentation claims match measured evidence.

**Architecture:** Keep policy and models independent of Home Assistant, HTTP, persistence and image adapters. Inject semantic ports at the composition root; reuse a single installation snapshot and preserve entry isolation, cancellation ownership and provider cooldowns.

**Tech Stack:** Python 3.14, Home Assistant 2026.11.2 validation baseline, pytest, coverage.py branch coverage, mypy, Flake8 and local AST architecture checks.

## Baseline and safety

- [x] Record clean `develop` baseline `d6b14df` and create `feature/project-quality-audit`.
- [x] Run the complete pinned suite: 1,358 passed; integration coverage 84.04% lines / 73.32% branches / 81.95% combined.
- [x] Run type, critical lint, architecture, dependency and distribution gates successfully.
- [x] Complete the audit offline; send no alarm commands or cloud probes.

## Architecture and behavior

- [x] Reproduce duplicate installation reads in placeholder generation with an offline coordinator test; pass camera identifiers from the existing snapshot, then assert one detailed read per refresh.
- [x] Move placeholder Pillow/filesystem work behind `CameraPlaceholderStore` and snapshot persistence out of `core/application`; verify real temporary-directory round trips and failure isolation.
- [x] Replace substring import checks with AST checks and synthetic forbidden-import fixtures, including relative imports and all core domain models.
- [x] Make `get_status` fail visibly on an unknown installation or failed refresh; verify blocking HA service calls.
- [x] Reproduce and correct ConfigManager envelope round trips and nested-default mutation using real temporary JSON files.
- [x] Reject nonpositive or too-short scan intervals in options, and safely normalize previously saved invalid intervals at coordinator initialization.

## Runtime and privacy

- [x] Reproduce malformed-but-valid session JSON (`null`, list, wrong field types), recover authentication without retaining invalid state, and cover disk reload once per session manager.
- [x] Remove the accidentally tracked CLI device artifact and prevent new per-user device files from being tracked; scan tracked names as well as contents without printing identifiers.
- [x] Inspect auth, cameras, alarms, notifications, cancellation, persistence and lifecycle code; record remaining risks as explicit findings, not unsupported guarantees.

## Documentation and reproducibility

- [x] Unify local setup, Makefile, shell helper and CLI developer commands around `.ha-2026.8-venv/bin/python`, preserving `HA_PYTHON` overrides.
- [x] Correct README, event reference, dependency injection guide, service descriptors and broken local links.
- [x] Render template examples with the pinned HA engine and validate automation schemas; use the sensor timestamp value when measuring staleness.
- [x] Preserve historical audit receipts; update current quality status, architecture decisions, SDDs and the new audit report with actual limitations.

## Current-version security follow-up

- [x] Follow the owner’s instruction to retire 2026.8.1 support and focus exclusively on current HA 2026.11.2. Historical receipts remain unchanged.
- [x] Use the matching official pytest-homeassistant harness, Probatio schemas and current HA dependency pins.
- [x] Bound JWT metadata and preflight image containers before decoding; add adversarial, bounded regressions.
- [x] Export the declared runtime dependency closure and audit its public versions without sending private data.

## Release verification

- [x] Run the full suite with line and branch coverage, including separate CLI/script measurements; retain the existing 100% notification gate and add a repository regression baseline.
- [x] Run type checking, critical lint, architecture/import, documentation, dependency and distribution gates against the final tree.
- [x] Review the complete diff, update the evidence report and clean only this iteration's owned temporary outputs.
- [x] Prepare the reviewed source and verification evidence for the authorized PR workflow. GitHub records the develop merge and the existing develop → master promotion status.

Verification commands (set `HA_PYTHON` to an existing pinned interpreter when using an external environment):

```sh
TMPDIR=/private/tmp make test-ha-2026-11 HA_PYTHON=/private/tmp/my-verisure-current-ha-venv/bin/python
make type-check lint-critical git-check distribution-check HA_PYTHON=/private/tmp/my-verisure-current-ha-venv/bin/python
TMPDIR=/private/tmp make coverage HA_PYTHON=/private/tmp/my-verisure-current-ha-venv/bin/python
```

All new behavior must have a reproducer that fails before its fix and passes afterward. Coverage percentages describe executable paths, not a guarantee that a third-party alarm service cannot fail.

# Manual Home Assistant verification

This document defines the manual verification that complements the deterministic
pytest harness. The default lifecycle checklist uses an isolated Home Assistant
Core 2026.8.1 instance. Household/provider tests require separate explicit owner
authorization and a bounded procedure; they are never an automated gate.

## Automated evidence already covered

The repository currently executes the real Home Assistant config-entry manager
through `pytest-homeassistant-custom-component` and verifies:

- user config-flow form and installation selection;
- invalid credentials and connection-error mapping;
- config-entry setup and unload;
- two concurrent entries with isolated coordinators, composition roots,
sessions, credentials, and storage paths;
- platform setup and unload;
- service registration and removal;
- diagnostics/import smoke checks.

These tests use synthetic credentials and never call Verisure.

## Manual checklist for an isolated instance

1. Create a disposable HA Core 2026.8.1 environment with no household backup,
   auth state, database, or credentials.
2. Install the integration from the repository checkout under
   `custom_components/my_verisure`.
3. Restart HA and confirm the integration loads without import errors.
4. Add one entry through **Settings → Devices & services**. Confirm the form,
   validation errors, and installation-selection step are actionable.
5. Add a second synthetic entry and verify both entries remain visible and
   independent after reload.
6. Verify the integration creates the expected alarm, sensor, binary-sensor,
   camera, and button platforms for the fixture/backend used by the isolated
   environment.
7. Reload one entry and confirm the other remains loaded.
8. Remove both entries and confirm services and entities are cleaned up.
9. Open diagnostics and verify that usernames, passwords, OTPs, session hashes,
   refresh tokens, and authorization material are redacted.
10. Record the HA Core version, integration commit, result of each item, and
    any sanitized error message. Do not commit HA storage, tokens, logs, or
    authentication state.

## Current limitation

No live Verisure call is part of the automated gate. Prefer a dedicated test
installation. For an explicitly authorized household session, record permitted
modes, original state, active pause instructions and command spacing; never infer
permission for total mode from permission for partial night. Restore the agreed
state and keep rollback material private. Do not retry ambiguous mutations
automatically or bypass provider cooldowns.

The isolated container checklist was not executed in this iteration. The pytest
harness against HA Core 2026.8.1 supplies deterministic lifecycle evidence.
Separately, the owner-authorized 2026-11-22 session used the actual HA UI and
official native application; see the [validation report](../validation/2026-11-22-live-verisure.md).
Neither evidence set substitutes for the other.

## Follow-up implementation evidence

The specification catalog records implemented contracts, regression tests and
outstanding acceptance decisions. Update the dated report after a live session
without adding raw traffic, account identifiers or authentication state.

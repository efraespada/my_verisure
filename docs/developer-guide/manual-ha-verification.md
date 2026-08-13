# Manual Home Assistant verification

This document defines the manual verification that complements the deterministic
pytest harness. It must be executed against an isolated Home Assistant Core
2026.8.1 instance, never against the household installation.

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

No live Verisure end-to-end call is part of the automated or manual gate in this
repository. A real-provider check requires a dedicated test account and must
be approved and run outside the household HA instance. The absence of that
check is reported explicitly rather than replaced with synthetic success.

The current development host has Docker installed but the active operator does
not have permission to access `/var/run/docker.sock`. Therefore the disposable
HA process/container checklist has not been executed here. The pytest harness
against the pinned HA Core 2026.8.1 environment remains the verified lifecycle
evidence; it must not be conflated with manual UI or provider validation.

Diagnostic detail: Docker Engine 29.6.2 is installed and the socket is owned by
`root:docker` with mode `0660`; the active user is not a member of `docker`. No
permission or host configuration changes were made by the validation process.

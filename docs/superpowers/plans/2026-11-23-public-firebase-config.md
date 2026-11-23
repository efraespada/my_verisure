# Public Firebase configuration handling

> Execute inline: preserve the validated receiver and pending develop/master PR flow.

**Goal:** Remove the provider client API-key literal from current source, retain credential reuse and document the security alert accurately.

**Architecture:** An HTTPS-only adapter discovers the same-origin main script from the public Verisure entrypoint, parses configuration without executing JavaScript, checks the known project/app/sender, and returns the client key only in memory. Receiver startup with valid durable credentials skips this adapter; new registration or actual MCS rejection may use it. Failure retains polling.

**Files:** `core/api/public_push_config.py` for discovery/parsing; `push_config.py` for non-secret identifiers and entrypoint only; `push_receiver.py` for lazy configuration; focused synthetic tests; security note and SDD updates.

- [x] Add failing parser/discovery tests: valid same-origin main asset, rejected foreign/insecure/ambiguous asset, matching project/app/sender, rejected malformed or foreign config.
- [x] Implement bounded credential-free HTTPS reads and parsing; never log or commit the returned client key.
- [x] Keep cached startup free of configuration HTTP requests. Resolve configuration before new registration and after actual MCS authentication rejection.
- [x] Run focused and complete tests, type/lint/dependency/distribution gates; verify the live public configuration without account login or alarm operations.
- [ ] Update security documentation/SDDs, amend the pending PR with the corrective commit and check CI before the authorized develop merge.

Verification commands:

```bash
TMPDIR=/private/tmp /private/tmp/my-verisure-validation-venv/bin/python -m pytest custom_components/my_verisure/core/tests/unit/test_public_push_config.py custom_components/my_verisure/core/tests/unit/test_push_receiver.py -q --no-cov
TMPDIR=/private/tmp HA_PYTHON=/private/tmp/my-verisure-validation-venv/bin/python HA_CORE='' ./scripts/test-ha-2026.8.sh
make type-check lint-critical git-check distribution-check HA_PYTHON=/private/tmp/my-verisure-validation-venv/bin/python
```

The alert's original commit remains historical evidence. Never claim that the provider key was revoked, that its Cloud restrictions were inspected, or that history was erased. Keep secret scanning enabled.

## Verification evidence

- Initial parser tests failed because the new adapter did not exist; focused tests passed after implementation.
- Complete coverage run: 882 passed, 90% aggregate (14,554 statements; 1,519 missed). Mypy: 264 files.
- Live public discovery: two unauthenticated HTTPS GETs matched the original public client value; no account calls, receiver registration or alarm commands. See `docs/validation/2026-11-23-public-firebase-config.json`.
- Existing Validate with HACS workflow re-enabled after GitHub disabled it for inactivity. Remote PR validation follows the corrective push.
- Initial remote Python runs failed during interpreter setup: Ubuntu 26.04 lacks a Python 3.14.4 distribution. The official actions/python-versions manifest confirms Ubuntu 24.04 support, so the Python job is pinned to that image. HACS passed independently.
- The next clean remote run exposed a missing `firebase-messaging` target requirement; the local environment already had the manifest dependency installed. Add its existing production pin to `requirements-ha-2026.8.txt` so the documented fresh installation matches production imports.
- Historical installed HA timings predate this bootstrap correction. No new household deployment is claimed.

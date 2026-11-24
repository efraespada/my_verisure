# App functionality audit and future specifications

**Goal:** Evaluate the meaningful functions of the official Spanish web and native
My Verisure clients and record independently implementable future contracts in
SDDs. This iteration changes documentation only; it does not add runtime features,
authorize a terminal or update the household installation.

**Architecture:** Keep the five existing as-built baselines distinct from future
capabilities. Describe semantic domain ports/use cases and HA adapters, explicit
permissions, bounded provider operations and privacy. Native bridge commands are
not HTTP endpoints and GraphQL document names are not standalone product features.

**Sources:** Official ES help, public web client 3.8.0 and inspected lazy modules,
sanitized read-only web observations, native WebView navigation and its public
bridge contract. Retain private material outside Git.

## Tasks

- [x] Inspect the current integration and specification standard.
- [x] Inspect web menus, key editor, installation, devices, sensor modes,
  delays, Wi-Fi and users; collect query shapes without account values.
- [x] Inspect native menus separately, including key editor, Conéctame,
  notification mailbox, app settings, profile and terminal authorization.
- [x] Confirm the native mailbox route is denied by the normal Chrome client;
  do not modify platform flags or grant additional permissions.
- [x] Classify every recovered GraphQL operation and native command into a
  product family, with source identity, evidence level and HA disposition.
- [x] Write the audit, coverage inventory and eleven Draft SDDs: shared management
  foundation, access/users, settings, routines, activity/inbox/incidents, camera
  media, smart locks, health/maintenance, protected administration and native
  personal-protection services.
- [x] Cover all twenty required sections, stable requirements, acceptance,
  synthetic test budgets, migration, cancellation, partial results and readiness
  blockers. Unknown protocols remain explicit gates, not invented API behavior.
- [x] Update the JSON/Markdown catalog, README, documentation navigation and
  current roadmap without marking future features implemented.
- [x] Run documentation, inventory consistency, section/traceability and privacy
  checks. Verify no runtime file or installed HA version was changed. Record the
  actual checks; historical runtime tests are not a fresh documentation gate.
- [x] Prepare reviewable documentation changes from develop, a PR description
  and the minimal source/evidence required for the later implementation.

## Initial validation receipt

`make docs-check HA_PYTHON=<current-HA-environment>/bin/python` and
`git diff --check` passed. The one-off offline audit check confirmed fifteen
catalog entries (five baselines, ten Drafts), twenty sections per Draft, seventy-five
requirements with acceptance/traceability, 263 classified documents, 152 commands
across twenty native handlers and twelve matching public source hashes. Common
private-data patterns returned zero matches; manual content review supplements
that check. No runtime file, manifest version or installed HA deployment changed.
Future runtime tests and coverage remain unimplemented. The public inventory
records the same scope and limitations.

## Configuration follow-up after the user screenshots

- [x] Contrast the seven screenshots with existing requirements and source.
- [x] Traverse the complete native device list and representative family details;
  inspect independent modes, scoped chime and manual Wi-Fi without saving.
- [x] Inspect comfort/presentation settings, visits, routine/reminder forms,
  failure-only notification preference and the empty battery-workflow list.
- [x] Add `specs/physical-device-inventory.md`; expand settings, routines and health.
- [x] Add `docs/technical/2026-11-24-configuration-screen-audit.md`, mapping all
  thirty-nine menu/screen/control rows to requirements and evidence limits.
- [x] Recover all 278 textual variants at 295 occurrences for the same 263 names;
  preserve differing selection sets and correct DIYInit/DIYCheck as mutations.
- [x] Verify the expanded sixteen-entry catalog, eleven Draft SDDs, eighty-four
  requirements, variant hashes, privacy, links and documentation-only scope.
- [x] Prepare the follow-up commit and updated description for the same PR;
  inspect CI after publication.

Follow-up verification passed: 39 screen/control rows, 84 traced requirements,
278 variants with exact source-slice/hash checks at 295 occurrences, twelve
matching source hashes, catalog/section checks, zero common private-data pattern
matches, `make docs-check` and `git diff --check`. All 26 changed files from the
base are documentation; the manifest remains 1.1.0. The follow-up does not claim
new runtime tests or validation of the UI workflows without eligible resources.

## Fixed live boundaries

No alarm command, saved installation/key/user edit, high-security terminal grant,
purchase, emergency request or new photo capture is part of this audit. The
household prohibition on interior-total arming remains in force. Live UI reads
must be spaced and bounded; no repeated requests to obtain an ambiguous result.

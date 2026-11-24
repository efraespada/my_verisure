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
- [x] Write the audit, coverage inventory and ten Draft SDDs: shared management
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

## Validation receipt

`make docs-check HA_PYTHON=<current-HA-environment>/bin/python` and
`git diff --check` passed. The one-off offline audit check confirmed fifteen
catalog entries (five baselines, ten Drafts), twenty sections per Draft, seventy-five
requirements with acceptance/traceability, 263 classified documents, 152 commands
across twenty native handlers and twelve matching public source hashes. Common
private-data patterns returned zero matches; manual content review supplements
that check. No runtime file, manifest version or installed HA deployment changed.
Future runtime tests and coverage remain unimplemented. The public inventory
records the same scope and limitations.

## Fixed live boundaries

No alarm command, saved installation/key/user edit, high-security terminal grant,
purchase, emergency request or new photo capture is part of this audit. The
household prohibition on interior-total arming remains in force. Live UI reads
must be spaced and bounded; no repeated requests to obtain an ambiguous result.

# Live Verisure validation implementation plan

> **For agentic workers:** Execute inline, task by task, under the user's existing authorization to diagnose, correct and update the integration.

**Goal:** Restore authentication and accurate alarm states, then verify exterior and partial-night commands against the provider web UI.

**Architecture:** Preserve entry-scoped sessions and fail-closed handling of unknown responses. Propagate actionable authentication errors to Home Assistant instead of swallowing them. Recognize only documented or directly observed complete alarm-state messages.

**Tech Stack:** Python 3.14, Home Assistant 2026.8.1 test harness, production HA 2026.11.2, pytest, Chrome.

## Constraints and baseline

- Never send interior total/away commands: the user is home.
- The user temporarily suspended live arm/disarm testing while on the terrace, then explicitly returned and authorized resuming exterior/partial-night tests. Total/away remains forbidden.
- Only exterior and/or partial night are authorized for live tests. Restore the initial disarmed state.
- Space provider operations; honor cooldowns. Tests use synthetic data and no network.
- Never commit credentials, tokens, SMS codes or raw household logs.
- Baseline: 753 passing tests with `TMPDIR=/private/tmp HA_PYTHON=/private/tmp/my-verisure-validation-venv/bin/python HA_CORE= make test-ha-2026-8`.
- Live evidence: latest published `c0f628e` cannot authenticate after moving storage; the UI shows a generic retry error. The provider web status query returns `alarm-manager.inactive_alarm` when both zones are disarmed.

## Task 1: Recover actionable authentication failures

Files: `core/session_manager.py`, `core/tests/unit/test_session_manager.py`, and coordinator boundary tests under `custom_components/my_verisure/`.

- [x] Add tests using `AsyncMock(return_value=AuthResult(success=False))` and typed OTP/connection/blocked exceptions. Assert rollback occurs, auth failures propagate as `MyVerisureAuthenticationError`, and connection/cooldown errors preserve their types.
- [x] Run the focused tests and observe failure before implementation.
- [x] Raise `MyVerisureAuthenticationError("Reauthentication required")` on rejected login results; after rollback, translate OTP/device authorization into that type and re-raise typed provider failures.
- [x] Verify the real coordinator converts the propagated error into `ConfigEntryAuthFailed`.
- [x] Deploy the verified patch with rollback copies and use HA's reauthentication form for SMS.

## Task 2: Interpret complete recognized states

Files: `core/application/alarm_status_service.py`, `core/api/alarm_status.json`, and `core/tests/unit/test_alarm_status_service.py` under `custom_components/my_verisure/`.

- [x] Add a parameterized regression using the bundled status config and `analyze_alarm_state({"data": result})`; expect disarmed for the observed inactive message and the appropriate state for each configured active combination.
- [x] Run it and observe unknown states before implementation.
- [x] Add an explicit inactive-message allowlist; only for known complete messages initialize all category statuses to `False` before setting matched active categories to `True`. Keep empty/unrecognized messages and missing configuration unknown.
- [x] Run focused and full tests, critical lint, architecture guard and distribution validation.

## Task 3: Live verification and measured follow-up

- [x] Recover the existing entry's session without deleting the entry or unrelated data.
- [x] Check disarmed state in HA against the native application's embedded web UI.
- [x] Activate exterior and partial night in HA, verify provider-confirmed state, then disarm. Record elapsed time and inspect sanitized errors.
- [x] Compare the same modes in the native UI with operations sufficiently spaced apart.
- [x] Address measured command/refresh latency after identifying the responsible stage and proving regression tests.
- [x] Reverify final disarmed state and record remaining limitations candidly.

## Native authentication evidence and implementation

- The official My Verisure 10.192.1 app was reset with the user's specific approval for its local credential entries. A fresh login returned `auth-api.mfa_needed`, a null hash and refresh token, and `needDeviceAuthorization: true`.
- SMS verification visibly reached “Dispositivo verificado”, then the home screen. Closing and reopening the native app and logging in again required no further SMS.
- Native login uses `OWI_10`, stable per-device IDs, app version 10.192.1, OS protocol version 27.2, `deviceUseBiometric: DISABLED`, and `phoneAsLogin: false`. The HA host's previous Linux OS string was rejected with provider code 66668.
- Successful native login returns `auth-api.login.success`, nonempty access and refresh tokens, and a nullable authorization flag. Only that observed positive combination is normalized to authorized.
- The integration now retains its own stable identity, uses the native profile, handles the tokenless SMS challenge, repeats native login after SMS, and attempts native token renewal before password login. Renewal's GraphQL contract comes from the official app's bundled `refreshLogin.graphql`; live renewal still needs verification.
- The first SMS webview exchange was encrypted in Proxyman. A domain-only temporary SSL rule was explicitly authorized and enabled for a later capture. Remove the added rule at the end. Do not claim that the initial SMS requests were captured.
- Regression verification: 781 tests pass; mypy, critical lint, architecture guard, distribution validation, and `git diff --check` pass.
- Thirteen changed production files were transferred and checksum-verified on HA. Rollback: `/config/.storage/my_verisure_rollback_20261122.tar.gz` (mode 0600). Package SHA-256: `411c41fe40c73af201266be7194519d856946ee34cba18d9ec49a52aeb641e40`.
- HA configuration check and restart, integration reauthentication, live renewal, permitted alarm tests, latency comparison, and final cleanup remain pending.


## Live progress after native contract comparison

- Current verified source: 798 passing tests; mypy (247 source files), critical lint, architecture guard, distribution validation and whitespace checks pass.
- Installed package: 26 production files; SHA-256 `2a571cbc60dff77015a4837c7ff17eb72fb0279ea160cf51a3c985ba4d448837`.
- HA SMS verification succeeded. Fixed zero-indexed phone IDs and propagation of explicit phone selection from the application layer into the provider client. No SMS code is stored in this document or repository.
- The actual HA access token expired after 900 seconds. Re-enabling the entry recovered a session without another SMS, with both access and refresh tokens changed and persisted. The native refresh contract is implemented; safe INFO messages now distinguish refresh from password fallback for the next verification.
- Native exterior arm/disarm completed successfully. The first attempt was rejected because the access token had expired six seconds earlier. After a fresh login, the server acknowledged `PERI1` and confirmed `E`; a separate `DARM1` operation confirmed `D`. Native polls occur at one-second intervals. Server response date differences were approximately one second for arm and three seconds for disarm; UI observations were upper bounds of 17 and 21 seconds respectively.
- The final native screenshot confirmed both zones disarmed. No total/away command has been sent.
- HA data loading exposed nullable `subtype`, `remoteUse`, and `isActive` fields. These now stay unknown through DTO/domain mappings instead of aborting the complete installation or fabricating booleans. Present cameras remain discoverable unless explicitly inactive; unknown metadata does not grant remote accessibility.
- Added `remoteUse` to the device query and the entry-owned UUID to the services query. The actual nested installation DTO accepts the 54 services captured from the official app; the separate legacy service DTO is not on that runtime path.
- A further live discrepancy was isolated: omitting the ES/es language context returns an empty services language. The regular authenticated header now retains the configured Spanish protocol locale. A query-projection regression reproduces the failure rather than returning full fabricated records.
- Manual alarm and camera operations now validate/renew authentication before provider calls. Arming obtains the provider's current `Status` instead of sending the fixed `E` value.
- HA general refresh is every 10 **minutes**, not seconds. One-second polling is bounded to an active operation, matching the captured native flow.
- Current HA state: latest package installed, HA restarting; entry temporarily disabled to avoid setup retries. Re-enable after startup, verify successful data loading, inspect refresh INFO evidence, then complete permitted live alarm tests and final disarmed verification.
- Pending cleanup: remove the temporary WebKit-domain SSL rule (leave pre-existing rules unchanged), remove owned raw captures and HA probe files, preserve sanitized evidence and the current rollback.

## Confirmed HA exterior command and cooldown follow-up

- The first HA exterior command started at 18:22:49 UTC and completed its provider confirmation at 18:22:50.901 UTC (about 1.8 seconds). The user independently confirmed the exterior was armed using a mobile connection.
- The redundant post-command `CheckAlarm`/`CheckAlarmStatus` path received HTTP 403 at 18:22:52 UTC. This left the UI displaying the previous disarmed snapshot despite successful physical arming. The integration entry was disabled to stop background calls. No provider calls should be made before 18:38 UTC (15 minutes plus a margin).
- Command polling now retains the provider's `protomResponse`. The coordinator publishes confirmed D/E states directly, without another panel check. Missing/unsupported confirmation invalidates stale state instead of retaining an old disarmed state. A provider error during an attempted command also invalidates the old state.
- Routine reads now use the native `Status` query for verified D/E codes. Other codes still use the strict legacy message interpretation rather than an assumed zone mapping.
- Camera entities now initialize the HA Camera base class. This resolves the reproduced `access_tokens` lifecycle failure. Cameras no longer trigger an extra coordinator refresh during platform setup.
- Current verification: 807 passing tests, mypy on 247 files, critical lint, architecture guard, distribution validation, whitespace checks.
- Installed package in progress: 28 production files, SHA-256 `6cd2c9eb51ae842999ee29e36851b271d9d69262adf805fa24584ec6673337a2`. Entry remains disabled during restart/cooldown. Physical exterior is currently armed, confirmed by the user; restore disarmed after cooldown.
- Registry follow-up: latest upstream changed device identity from installation ID to entry ID and camera identity from device code to list index without a migration. Live registry shows an old device with six stale entities, plus a new device with 20. Camera index/code collisions can associate an old entity ID with a different camera. This needs a stable opaque camera key and a careful registry migration preserving existing entity IDs and area/customization.

## Current result (supersedes earlier deployment/status notes)

- Latest installed patch: 32 production files, SHA-256
  `68854bde7dcb559b89ea859ee07124d9449dc8e7079f1cceb8e79a7e3e120baa`.
  Its file contents match the working source. HA verified the archive checksum
  before extraction and restarted successfully.
- Camera identity is now entry/type/code based and opaque. The original device,
  area, alarm entity ID and automation links were restored; HA has one device
  with 20 entities. Scoped registry APIs remove the observed deprecation warning.
- Native captures established Q=partial night and C=night plus perimeter, in
  addition to D/E. Supplementary exterior remains optional for both Night and Away;
  the owner's option is enabled.
- A disarm after token renewal failed with stale installation context. Reloading
  permissions with the unchanged token pair made the same operation succeed.
  Commands now bind installation permissions to the current access session and
  reject context-refresh failures/races before mutation.
- At 19:27 UTC the installed patch renewed an actually expired access token and
  completed Night+perimeter in about 4.0 seconds. The subsequent disarm completed
  in about 3.9 seconds including HA-side effects. Final HA state was fully
  disarmed, the entry remained enabled, and no integration ERROR/403 appeared in
  the post-restart log. Total/away was never exercised.
- The temporary `customers.verisure.es` SSL rule was removed. The pre-existing
  My Verisure application rule was retained. Diagnostic INFO overrides were
  returned to warning. Twelve owned HA temporary files and one obsolete source
  upload were removed; both private rollback archives were checked and retained.
- Three as-built SDDs, a template and catalogs were added using the inspected
  `vypdev/copilot` structure as a reference. No Copilot SDK/workflow was installed.
- Final automated evidence: 825 tests passed; 89% measured coverage; mypy on 250
  files; critical lint, architecture, dependency and distribution checks passed.
  Catalog paths, specification sections and documentation links were checked.
- Home is confirmed as exterior-only PERI1. Fresh camera photo parity is not
  established: native navigation returned to login or lost its accessible window;
  user assistance to leave the camera section visible was requested. No camera
  polling acceleration was inferred without protocol evidence.

See [the sanitized validation report](../../validation/2026-11-22-live-verisure.md)
for exact evidence boundaries and selected timestamps.

## Camera follow-up — owner-authorized continuation

- The owner confirmed Home remains exterior-only PERI1. Preserve that mapping.
- Interior total/away remains forbidden; camera work requires no alarm writes.
- [x] Capture one native fresh-photo request, bounded polling and full retrieval;
  compare actual variables, headers, nullable responses and timing to the client.
- [x] Reproduce camera polling-budget loss across coordinator, use case,
  repository and client with a synthetic bounded transport test before fixing it.
- [x] Correct proven protocol/orchestration defects. Preserve the effective
  20-second polling rate unless captured native evidence supports another value.
- [x] Validate image identity, freshness and failure reporting without replacing
  prior real images with placeholders or implying old photos are new captures.
- [x] Run focused/full tests and release gates, deploy with rollback, verify a
  bounded HA image journey, restore temporary capture settings and update SDDs.

### Verified camera result and push boundary

- Camera follow-up: 834 tests passed; 89% coverage (13,450 statements, 1,465
  missed); mypy on 251 files and all release gates passed. The initial coverage
  run used a macOS symlinked temporary root; the canonical `/private/tmp` run
  passed the existing path assertion.
- Installed 39 production files after checksum verification and a source rollback;
  `ha core check` and restart succeeded. Archive SHA-256:
  `3aefc3cefd9056fc19b09a93fbff5f6d1e4b3387ccb61722ca3eb06bc5492207`.
- The native sample produced a photo notice in about 21 seconds. One selected
  HA camera produced three JPEGs plus a thumbnail in 24.88 seconds, with a fresh
  provider timestamp and a real image visible in the camera dialog. These were
  different cameras, so the timings are observations, not a controlled benchmark.
- HA retained 20 entities and original IDs; default aliases were visible, and
  protection was disarmed. No alarm mutation was issued during this follow-up.
- Restored temporary logger levels, removed two HA uploads, retained all three
  private rollback archives and removed only the added domain SSL rule.
- A private FCM probe registered/authenticated on macOS and in an ephemeral Linux
  container. After explicit approval, a separate Indigitall device and Android
  FCM token registration succeeded. The later Android-profile experiment below
  established real delivery.
- Account binding subsequently completed in independent scratch identity/storage
  after explicit authorization and a new SMS. No old SMS answer was reused.
- Production push dependencies and entry lifecycle are unchanged. Follow
  [the push investigation](../../technical/push-reception-investigation.md) before
  implementing or advertising delivery support. Placeholder/freshness UX and
  exhaustive camera-family coverage remain separate acceptance work.

### Subsequent receiver verification

- Owner authorization covered binding the independent device; the latest SMS
  verified it. The first completion raised a device-authorization error, followed
  by a successful single registered-device login without another SMS. Its own
  session is persisted outside HA. The failing response was not captured.
- Two one-camera photo experiments retrieved three fresh images each, with one
  initial status read and one delayed fallback. No MCS data arrived during either
  75-second window. The second followed a specifically approved `externalCode`
  association, accepted by Indigitall. Those attempts did not prove push delivery.
- Native capture comparison proves `idDevice` equals the APNs notification token.
  The probe instead supplied a generated identifier at login. A separate Android
  token/profile experiment was then explicitly authorized, with its prior private
  session retained for rollback. The result is recorded below.
- Receiver tasks from the completed experiments were stopped cleanly. No HA
  configuration, dependency, source deployment or alarm command changed during
  these isolated experiments.

### Completed Android-profile receiver proof

- Login with the real FCM token as `idDevice` and `OWA_10` was accepted without
  another SMS. A returned token confirmed the Android profile and the probe
  retained its own UUID/storage, separate from HA.
- The first event arrived in Linux in 19.104 seconds. A fixed-layout Crypto-Key
  parser failed on combined `p256ecdsa`/`dh` parameters; the preserved encrypted
  envelope was decoded offline and correlated with the exact fresh photo signal.
- Four synthetic encrypted round trips reproduced the old failure and verified
  named-parameter parsing, header ordering/quoting/whitespace and padding.
- The next spaced photo request completed automatically: Linux received/decrypted
  its hint in 18.582 seconds and the Python client committed three matching fresh
  images by 20.156 seconds. One initial status read; no fallback status read.
- Listener/decryption ran in Linux; orchestration/retrieval ran on the Mac.
  The actual HA push runtime and production lifecycle were not exercised. All
  listeners stopped cleanly and no alarm command was sent.
- Added a sanitized receipt and a fourth, Draft SDD for production profile/session
  migration, registration, decoder ownership, correlation, fallback and lifecycle.
  No FCM dependency or receiver was added to the installed HA integration.

### Preserve the validated decoder as an experimental artifact

- [x] Extract the proven pure decoder into `experiments/linux_push/`, with no
  network, household fixture, credential loading or HA runtime dependency.
- [x] Preserve the four synthetic encrypted round trips and upstream-failure
  reproduction as an explicit optional check, using isolated pinned dependencies.
- [x] Verify the extracted functions match the live-tested decoder, rerun that
  check and lint, update catalog links and scan changed files for private values.

# Controlled live validation — 2026-11-22

Historical campaign record: the prototype-stage limitations below refer to
2026-11-22. The [2026-11-23 receipt](2026-11-23-ha-push.json) and
[current catalog](../../specs/CATALOG.md) supersede its production-push gap.

Status: alarm fixes validated for exterior, partial night and disarm; camera
follow-up installed and a selected fresh capture verified in HA. Remaining
acceptance boundaries are listed below. Times are UTC.

## Environment and authorization

- Source base: `c0f628e8ee0e4835054cd56eb9e27b84eec8b9d7`, branch
  `feature/live-verisure-validation`; changes are local working-tree changes.
- Actual host: HA Core `2026.11.2`, HAOS `18.4`.
- Official comparison: native My Verisure `10.192.1` and its embedded web flow,
  observed through owner-authorized Proxyman capture.
- The owner permitted exterior and partial night. Interior total/away was
  forbidden throughout because the owner was home. Terrace pauses were honored.
- The existing HA config entry, alarm entity ID, device identity, area and
  automation links were preserved. Final observed state: fully disarmed.

No account identifier, installation number, address, phone, OTP or token belongs
in this report. Raw captures remain private and are not test fixtures.

## Protocol evidence and corrections

| Area | Observed native contract | Implemented correction |
|---|---|---|
| Authentication | native login/refresh; stable device identity; embedded web SMS followed by native login | current profile/headers, strict accepted-response classification, phone ID zero, device-bound challenge and transactional token persistence |
| Installation | service request includes device UUID; nullable device/service metadata | matching request fields, strict identity validation and nullable optional fields |
| State | cheap Status returns D/E/Q/C | recognize complete disarmed/exterior/night/night+exterior states without a radio check |
| Commands | ARMNIGHT1 from D gives Q; PERI1 from Q gives C; DARM1 gives D | use actual currentStatus, retain completion protomResponse and publish confirmed flags |
| Polling | command WAIT polls about one second apart | bounded one-second command polling; separate legacy radio polling stays at 15 seconds |
| HA lifecycle | camera base and existing registry identities must survive updates | initialize camera token state; remove duplicate setup refreshes; migrate identity without replacing original entities |
| Session renewal | cached installation permissions can become stale when the access session changes | bind permissions to the current access session; refresh before commands on mismatch/expiry and reject races before mutation |

The supplementary perimeter option is retained for both Night and Away. It is
false by default for new entries and enabled in the owner's validated entry.

## Selected live observations

| Time | Journey | Result |
|---|---|---|
| 17:29–17:30 | Native exterior, then disarm | E and D confirmed |
| 18:22 | HA exterior followed by redundant radio check | arm succeeded in about 1.8 s; extra check received HTTP 403; owner independently confirmed exterior active |
| 18:41 | HA disarm after provider cooldown | D confirmed in about 2.6 s; redundant check removed |
| 18:49 / 18:53 | Native partial night, then exterior | Q and C confirmed; total never selected |
| 18:55 | Native disarm | both interior and exterior disconnected |
| 19:10 | HA Night with supplementary perimeter | C confirmed in about 3.7 s |
| 19:12 | HA disarm immediately after token renewal | rejected with stale installation context; HA correctly displayed unknown |
| 19:15 | Same-token experiment after installation reload | token pair unchanged; refreshed permissions made disarm succeed; D restored |
| 19:27:47.613–19:27:51.620 | Latest installed Night+perimeter after actual token expiry | refresh token renewed access in about 118 ms; fresh context and both commands completed in about 4.0 s; C shown |
| 19:28:48.141–19:28:51.997 | Latest installed disarm | provider completion about 2.6 s; HA-side completion about 3.9 s; D shown |

The initial one-second policy was incorrectly extended to legacy radio status
checks during investigation. This was corrected to 15 seconds after the 403;
the entry was disabled during a provider cooldown longer than 15 minutes. No
rapid mutation retry was used to work around the block.

These are single observations, not a latency guarantee. Native HAR connection
timing can include reused connections; HTTP Date is only an approximate event
time. HA service logs establish the subsecond figures above.

## Installed source and rollback

The latest patch archive contained 32 production files and was checksum-verified
on HA before extraction and restart:

`68854bde7dcb559b89ea859ee07124d9449dc8e7079f1cceb8e79a7e3e120baa`

Private integration/session and device/entity registry rollback archives were
retained on HA. The rollback source archive does not reverse physical alarm
state; that requires a separately authorized command.

## Automated verification

The Python 3.14.6 / HA Core 2026.8.1 test environment passed 825 tests. Its coverage
run measured 89% (13,290 statements, 1,466 missed). Mypy passed across 250 files;
critical lint, architecture, distribution and diff-whitespace checks passed.
Synthetic tests cover malformed authentication, challenge binding/expiry, token
persistence rollback, session-context races, current-status mapping, confirmation,
unknown-state behavior and real HA registry migrations.

The camera follow-up passed 834 tests with 89% coverage (13,450 statements,
1,465 missed), mypy across 251 files, critical lint, architecture, dependency,
distribution and whitespace gates. One initial coverage run exposed the existing
macOS `/var` versus `/private/var` temporary-path assertion; rerunning with the
canonical `/private/tmp` validation root passed. No provider calls occur in tests.

## Camera follow-up and Linux push investigation

The owner confirmed Home remains exterior-only PERI1 and manually left the native
camera section visible. A single fresh native photo was requested around
19:57:25. The first `RequestImagesStatus` response was accepted but still
processing, with null `status` and `numinst`. Around 19:57:46 the app displayed
a photo notice and fetched a thumbnail by `idSignal`; opening it at 19:58:12
fetched three full images. This establishes the native request/retrieval sequence,
not successful HA capture. No alarm mutation was sent during camera work.

The request mutation and initial status query match the integration's selections
apart from `__typename`. Optional media fields are omitted for the current panel
in both clients. Initial gallery thumbnail responses can contain only null fields.
The native gallery also reads camera capabilities through `mkGetAllCameras`;
the integration's present YP/YR discovery comes from its device list. Capturing
one installation does not establish support for every camera family.

Proven local fixes forward polling budgets through all boundaries, allow an
entry-owned single camera selection, reject overlapping refreshes, keep the
button busy until completion, propagate failures, notify existing entities after
successful refresh and use provider aliases for default display names. The
effective polling interval remains 20 seconds. Existing entity IDs/custom names
and prior committed photos are retained.

The 39-file camera archive was checksum-verified on HA, extracted after a private
source rollback was saved, and passed `ha core check` before restart:

`3aefc3cefd9056fc19b09a93fbff5f6d1e4b3387ccb61722ca3eb06bc5492207`

After restart, HA loaded the original 20 entities with provider camera aliases
and fully disarmed alarm state. A selected-camera action began at 20:46:02.956;
one `RequestImages` mutation was accepted, and two status reads were spaced
20 seconds apart. The second confirmed completion at 20:46:24.259. Three JPEGs,
a thumbnail and the atomic commit marker were stored by 20:46:27.832, with a
provider capture timestamp of 21:46:19 local time. The HA camera dialog displayed
the real image. Total use-case time was 24.88 seconds. Other camera directories
were not updated. This and the native 21-second observation are separate samples
from different cameras, not a controlled latency benchmark.

An isolated Python FCM receiver registered and authenticated to Google's MCS
with a Chromium/Linux profile on the Mac and then inside a local Linux container.
The actual HA runtime remains untested. With specific
owner approval, Indigitall accepted a new Android-routed SDK device (201) and its
independent FCM token (200); no existing native token was replaced. The official
Android SDK source identified the required package-name header after an initial
401. The probe subsequently completed SMS verification and an accepted native
login persisted its independent session. Two isolated one-camera requests each
retrieved three fresh images, but neither produced an MCS notification within
75 seconds. Updating the specifically authorized SDK `externalCode` did not
resolve that delivery gap. No production push implementation was installed.

Further comparison established that the native login `idDevice` equals its APNs
push token, while the probe had used a generated identifier at login. An Android
profile experiment using the FCM token in that field was subsequently accepted
and delivered real events, as described below. The initial OTP completion raised an authorization
error before the subsequent accepted login; its exact response was not captured,
so no new production authentication fix is inferred from that observation. See
the [push investigation](../technical/push-reception-investigation.md).

## Validated Linux receiver prototype

With explicit owner authorization, the independent probe sent its FCM token as
`idDevice` and used `OWA_10`. Login succeeded without another SMS; the returned
token confirmed that profile. The first photo-ready event reached Linux in
19.104 seconds. Its preserved payload was decoded offline after identifying a
fixed-layout Crypto-Key parser defect in firebase-messaging 0.4.5.

The corrected probe parsed named `p256ecdsa`/`dh` and salt parameters and
normalized base64url padding. Four synthetic encrypted round trips reproduced
the original failure and passed with the correction. A second live experiment
then received/decrypted the event automatically in 18.582 seconds. Authoritative
reads by its exact signal ID verified the expected installation, selected camera,
photo signal type 16 and fresh timestamp; three images were committed by 20.156
seconds from the request. It used one initial status read and no fallback status
read. The two Android-profile photo requests were spaced apart.

The listener/decryption ran in Linux aarch64/Python 3.14.6; orchestration and
image retrieval ran in Python on the Mac. This is not an actual HA push runtime
test. Dependencies remained isolated, the original HA entry/profile stayed
unchanged and no alarm command was issued. The receiver was stopped cleanly.

The [sanitized machine-readable receipt](2026-11-22-linux-fcm.json) records the
measured scope and pins. The [draft specification](../../specs/linux-push-photo-completion.md)
defines production acceptance. Cold-start account-identifier derivation,
maintained decoder/dependencies, entry lifecycle, profile migration,
deduplication and fallback still need implementation and HA runtime validation.

## Remaining acceptance boundaries

- Home remains exterior-only PERI1, explicitly confirmed by the owner during
  the camera follow-up. Existing automation behavior is preserved.
- Total/Away and partial day remain untested live. The owner reserved total
  verification for a later suitable session.
- Native and selected-camera HA fresh-photo capture/retrieval are observed.
  Broader camera-family coverage, placeholder/image-age presentation and
  production HA push integration remain open. Isolated Linux reception and
  exact photo correlation are now demonstrated.
- Camera refresh forwards interval/attempt parameters; its effective default
  remains 20 s. Matching native completion efficiency requires proven push
  reception, not an assumed one-second photo polling interval.
- Dedicated alarm command serialization, compound-command recovery, snapshot
  freshness and complete sensor localization require further review.

The [three baseline specifications and push draft](../../specs/README.md) describe
implemented contracts, proposed work and these limitations. No future Copilot
tooling was installed.

## Session cleanup

The temporary domain-wide SSL decryption rule was removed after the alarm session,
re-enabled for the authorized camera capture and removed again afterward; the pre-existing
native application rule was retained. Diagnostic logger overrides were returned
to warning. Twelve owned HA temporary probe/upload files and one obsolete source
upload were removed; both rollback archives were rechecked and retained. The
integration remained enabled with 20 entities and all protection zones disarmed.

The camera follow-up also restored its temporary logger overrides to warning,
removed its two source upload files and retained the three private rollback
archives. The camera source rollback is 629,604 bytes with mode 0600. The original
device page was left available in the Chrome test group. No alarm command was
issued during this follow-up.

Redundant private HAR exports were removed only after confirming that every
request/response record was contained in the retained private native-modes export.
Unique login/mode evidence remains private for the outstanding protocol review.
The working validation environment is retained for the remaining acceptance
decisions; its duplicate download cache was retired. Source hashes and Git state
were verified unchanged by cleanup.

## Subsequent production push campaign — 2026-11-23

The later [HA push receipt](2026-11-23-ha-push.json) supersedes the earlier
production-push limitation above. It records an installed FCM capture, a separate
disabled-receiver polling capture and the remaining restart check. That campaign
issued no alarm commands; its times use Europe/Madrid offsets explicitly.

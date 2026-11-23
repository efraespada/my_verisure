# Linux push reception and photo completion

- Status: As-built baseline; installed push, polling and restart verified
- Date: 2026-11-23
- Catalog capability ID: linux-push-photo-completion
- Last verified: 2026-11-23
- Owners: My Verisure maintainers
- Scope: optional entry-owned FCM reception and photo completion
- Required review gates: behavior, architecture, tests, privacy and actual HA runtime
- Remaining evidence: broader camera/Android app coverage and transient provider failure causes

## 1. Executive summary

The installed HA integration receives photo-ready notifications without Apple
notification APIs. One controlled HA request committed three fresh images in
21.13 seconds using push and no second status read. With the receiver disabled,
a subsequent accepted request committed three images in 45.07 seconds through
three status reads at the unchanged 20-second interval. These are individual
observations, not an SLA or a controlled native-app benchmark.

## 2. Problem, current behavior and evidence

Polling may read just before a photo becomes ready and then wait another full
interval. FCM wakes the existing request so it can retrieve the exact signal.
An isolated Linux receiver previously demonstrated 18.582-second automatic
delivery and 20.156-second image commit with Mac orchestration. A fresh token
never registered with Indigitall also received delivery and committed images
in 20.147 seconds. Production therefore needs no captured account identifier
or Indigitall registration. Actual HA evidence is recorded separately in
[the installed receipt](../docs/validation/2026-11-23-ha-push.json).

## 3. Actors and terminology

The owner opts in on an existing HA config entry. Google registers an independent
FCM receiver; Verisure associates its token through native authentication.
A hint is an authenticated notification, not proof that an image is ready.
A committed capture includes the thumbnail, all expected images and the existing
completion marker for the selected camera.

## 4. Goals and non-goals

Reduce photo completion latency while retaining bounded polling, registry
identity, entry UUID, provider cooldowns and private credentials. Notifications
never issue alarm commands or refresh an entire installation. This capability
does not publish arbitrary notification text or implement push-driven alarm
state updates. No inbound port or Firebase server credential is needed.

## 5. Functional requirements

- PUSH-1: store and reuse one independent receiver per enabled entry.
- PUSH-2: use its token as `idDevice` and a consistent OWA profile for login,
  refresh, SMS and data headers without changing unrelated identity.
- PUSH-3: authenticate/decrypt combined `Crypto-Key` headers with normalized
  base64url padding; reject invalid or unsupported messages safely.
- PUSH-4: accept hints only for an active request and matching installation/time.
- PUSH-5: verify the authoritative thumbnail signal, camera and freshness before
  retrieving and committing that exact photo signal.
- PUSH-6: deduplicate and bound hints; a hint never creates a photo mutation.
- PUSH-7: drain entry tasks on unload, reuse credentials and retain polling when
  registration, transport or notification delivery is unavailable.
- PUSH-8: expose only safe counters/state in diagnostics and meaningful HA errors;
  never expose account credentials, raw payloads or image data in public attributes.
- PUSH-9: resolve public client metadata only for registration or actual MCS
  authentication recovery, validate its trusted origin and known project, and
  keep the provider client-key literal out of source and durable receiver state.

## 6. Data and state contract

`PhotoNotifications` owns one pending request and at most 128 recent delivery IDs.
Messages contain JSON in `data.text`. Only `request: INF`, `type: 0`, a matching
installation, a numeric signal and a timestamp within the pending window can
wake the request. The event timestamp may precede request start by at most two
seconds; future timestamps beyond 60 seconds are rejected. Idle hints do nothing.

`mkGetThumbnail` is queried by `idSignal`; signal type 16 and the selected `YR` or
`YP` device code must match. Its observed Spanish local timestamp must fall
between request start minus five seconds and current time plus 60 seconds.
`mkGetPhotoImages` must return exactly the selected device. All expected image
writes must succeed before the existing completion marker is published.

## 7. User-facing configuration

`push_enabled` defaults to false and is labeled immediate photo updates. The
setting explains that ordinary polling remains enabled and SMS may be needed.
Enabling preserves the existing entry, entity IDs and UUID. Disabling stops the
listener while retaining the verified Android profile, token and session so
polling continues and re-enabling can reuse credentials.

No native capture, `externalCode`, Indigitall app key or owner-entered Firebase
configuration is required. Public project/application/sender identifiers are
packaged from the official client. The client key is discovered automatically
from its public HTTPS entrypoint and same-origin main asset when needed; no
JavaScript is executed. These identify the public client rather than an account
or server credential. See the [security review](../docs/technical/firebase-client-configuration.md).

## 8. Clean Architecture design

| Boundary | Responsibility |
|---|---|
| API adapters | Google registration/MCS, authenticated decoder, native profile and GraphQL |
| Application | bounded hint scope, correlation and existing camera refresh workflow |
| Repository/use case | carry optional exact signal; retain legacy retrieval without a hint |
| HA adapter | options, shared HTTP session, entry startup/unload, safe diagnostics/errors |

The composition root owns profile, device/session managers, clients and broker.
Core modules import no HA APIs. Profile changes invalidate candidate in-memory
authentication; normal transactional authentication persists the accepted session.
A stored profile mismatch is checked before reusing an access session.

## 9. UI/UX and content contract

A successful capture updates the existing camera. A failed request retains its
previous image and raises a recognized Home Assistant error. Camera failures,
service blocking and authentication have English/Spanish translations. Provider
error strings are not copied into these user-facing messages. Camera selection
remains scoped to the entry and existing registry identity.

## 10. Failure, recovery and cleanup

The follow-up [general-notification audit](../docs/technical/notification-audit-and-design.md)
reproduced cancellation ordering and cached-crypto validation defects and identified
token-binding/ACK limits. Its implemented follow-up adds cancellation-safe
write ownership, cached credential validation and transactional token binding.
The [notification implementation receipt](../docs/validation/2026-11-23-notification-implementation.json)
records those corrections; the original photo-only tests do not establish them.

Durable credentials are reused directly on startup and transport reconnect. Only
an actual MCS login rejection requests HTTP registration recovery. This avoids
unnecessarily replacing a working registration after a transient check-in failure.
Fresh registration failure leaves polling available with a 15-minute setup backoff.
Public configuration discovery uses at most two GETs, each bounded to 15 seconds,
with 1 MiB HTML and 16 MiB script limits. Unexpected origins, redirects, ambiguous
metadata or a different project/application/sender fail closed before registration.
Transport reconnection uses bounded 30-to-900-second backoff. Startup is bounded;
unload cancels and awaits SDK tasks even if SDK stop returns early. Persistent
state writes are coalesced and atomic. Cancellation always clears a pending photo.

No hint retains the existing request reference and polling budget. A rejected
hint waits out the interval rather than issuing another mutation. Provider 403
errors propagate to the existing cooldown mechanism. A generic rejection is
reported without automatic rapid retries. The live campaign observed one Google
registration rejection and one camera rejection; spaced retries succeeded, but
their precise causes were not established.

## 11. Security, permissions and privacy

TLS verification remains enabled. The owner authorized independent FCM registration,
native token association, installation and controlled tests. No phone's token or
SDK registration is replaced. Keys and delivery history use entry-owned atomic
JSON storage with mode 0600; filesystem I/O runs outside the HA event loop.
Sender/project, installation, signal, camera and time are checked. Public entities
and diagnostics contain no receiver token, secret key, raw event or private image.
The provider's public client key stays in memory when registration needs it.
Provider Cloud restrictions have not been inspected, and no provider key was
revoked or rotated. The original alerted commit remains historical evidence;
secret scanning remains enabled.

## 12. Observability and operations

Safe diagnostics expose connection state and reception/reconnection counters.
INFO logs distinguish push confirmation from status completion and image commit.
SDK verbose payload logging is disabled. Receiver delivery and photo persistence
are separate assertions. Temporary diagnostic levels are restored after testing.

## 13. Compatibility, migration, rollout and rollback

The dependency is pinned to `firebase-messaging==0.4.5`. A maintained local decoder
adapter fixes its combined-header parsing. The pinned HA 2026.11.2 test environment
passes dependency checks; the actual installed host is HA 2026.11.2/HAOS 18.4.
Production-only archives are checksum verified and configuration checked before
restart. Private pre-push source/session/registry rollback and the small error-UI
rollback are retained. The original 20 entities and device UUID are preserved.

## 14. Testing strategy and numeric budget

The original photo iteration passed 882 tests with its then-current 90% aggregate
coverage metric. See [current quality evidence](../docs/quality-status.md) for the
new production-only branch denominator and complete notification-module gate. Twenty-eight original
regressions cover profile isolation, private atomic writes, bounded hints,
authenticated decoding/tamper rejection, sender filtering, credential reuse,
failed startup, cancellation/task draining, exact camera/signal retrieval,
missing/wrong hints, freshness, 403 propagation, lifecycle, Android renewal and
safe service errors. Twenty further regressions cover public configuration discovery,
origin/status/size rejection, matching metadata, failure before registration and
cached startup without configuration HTTP. No unit test contacts the household or Google.

Actual HA tests use one selected camera, conservative pauses and zero alarm
mutations. Push and disabled-receiver polling commits are verified separately.
After a full restart, the same token and all entity identities were preserved;
a further push capture committed three images in 23.55 seconds. The 143 installed
source files matched that installed artifact, and the receiver error check was clear.
Those observations predate the public-configuration follow-up. That correction
has synthetic coverage and a live unauthenticated metadata comparison; it was
not reinstalled or exercised against household devices during PR preparation.
It was subsequently installed with the notification implementation: 153 source
files verified, unchanged token/UUID/original identities across restart/reload,
and a 23.22-second three-image capture producing correlated reported/confirmed
events. Fresh registration was not repeated. See the
[implementation receipt](../docs/validation/2026-11-23-notification-implementation.json).

## 15. Documentation and discoverability

Maintain this baseline, the capability catalog, configuration/camera docs,
technical investigation and sanitized runtime receipt together. Copilot tooling
is not installed. Historical prototype evidence remains labeled by runtime.

## 16. Acceptance scenarios

1. PUSH-1/2: isolated profiles, stable UUID, matching login/renewal and persisted state.
2. PUSH-3: encrypted combined headers decrypt; tampering and foreign senders fail safely.
3. PUSH-4/5: the pending camera's exact fresh signal commits all expected images.
4. PUSH-6: stale/foreign/duplicate/idle events cause no request burst.
5. PUSH-7: unload drains tasks; absent push keeps the original bounded polling workflow.
6. PUSH-8: safe diagnostics and recognized HA errors contain no private provider data.
7. PUSH-9: cached startup makes no configuration GET; invalid public configuration
   prevents registration and leaves polling available without a new account request.

## 17. Requirements traceability

| Requirements | Evidence |
|---|---|
| PUSH-1/2 | `test_push_components.py`, `test_push_lifecycle.py`, Android native renewal test and live OWA session |
| PUSH-3 | `test_push_receiver.py`, synthetic encrypted round trips and offline actual envelope decode |
| PUSH-4/5 | `test_push_camera.py`, live exact photo commit and private completion marker |
| PUSH-6/7 | broker/receiver/camera lifecycle tests and disabled-receiver live capture |
| PUSH-8 | safe service error tests, public entity redaction tests and bounded diagnostics |
| PUSH-9 | `test_public_push_config.py`, cached receiver/failure tests and sanitized public-source comparison |

## 18. Implementation or maintenance sequence

Keep the dependency pin and decoder adapter reviewed together. When changing the
SDK, rerun encrypted round trips and task ownership tests before deployment.
New notification kinds need their own authoritative correlation contract; do not
promote every INF event to an alarm state or photo completion.

## 19. Definition of Done

- [x] Independent Linux delivery and direct registration without Indigitall are demonstrated.
- [x] Production receiver/profile/broker/decoder and opt-in lifecycle are implemented.
- [x] Full offline checks, actual HA push and polling fallback pass.
- [x] Existing identity and private persistence are preserved.
- [x] Final restart/capture, normal logging and owned temporary-file cleanup are recorded.

## 20. References and decisions

See [the investigation](../docs/technical/push-reception-investigation.md),
[historical live validation](../docs/validation/2026-11-22-live-verisure.md) and
[installed receipt](../docs/validation/2026-11-23-ha-push.json). The current Android
native app was not exhaustively captured. Android profile constants were accepted
experimentally; this baseline does not claim complete native-app equivalence.

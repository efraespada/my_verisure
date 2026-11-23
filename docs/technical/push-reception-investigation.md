# Push reception on a Linux Home Assistant host

The [notification audit and proposal](notification-audit-and-design.md) catalogs
the official client's broader push handlers and current correctness gaps. Its
new event entities and reconciliation are proposed, not part of the installed
photo receiver. See the [source catalog](../validation/2026-11-23-notification-catalog.json)
and [synthetic audit evidence](../validation/2026-11-23-notification-audit.json).

The follow-up [Firebase configuration review](firebase-client-configuration.md)
removes the embedded public client key and resolves it only for registration
or actual MCS authentication recovery. Cached startup skips discovery. Its
unauthenticated public-source comparison is separate from the installed runtime
measurements below.

Status: optional production receiver installed; HA push and polling verified, 2026-11-23. Linux received and automatically decrypted a real
photo-ready event in 18.582 seconds; the Python probe retrieved and committed
its three fresh images by 20.156 seconds from the request. The listener/decoder
ran in Linux, while orchestration/retrieval ran on the Mac. See the
[push specification](../../specs/linux-push-photo-completion.md) and
[sanitized receipt](../validation/2026-11-22-linux-fcm.json).

## Evidence

The official My Verisure 10.192.1 iOS app registers its own device with
Indigitall. Its captured registration uses `platform: ios` and an APNs token.
The SDK device ID is also supplied as `idDeviceIndigitall` during Verisure
authentication. Topic subscription calls contain household/profile segmentation;
they do not establish a public photo-event subscription interface.

A single native photo request was accepted at approximately 19:57:25 UTC. The
app made one immediate `RequestImagesStatus` call, which returned `res: OK` and
`alarm-manager.photo-request.processing`, with null `status` and `numinst`.
At approximately 19:57:46 the UI received a photo notice and fetched
`mkGetThumbnail` by `idSignal`. Opening the notice fetched three images through
`mkGetPhotoImages`. The app's public web client also dispatches native
`pushMessageReceived` callbacks into its image workflow. This supports a push
completion path. Subsequent receiver experiments below recovered the notification
and correlated its exact signal with the requested camera.

Android's Indigitall SDK uses Firebase Cloud Messaging. Its
[official integration guide](https://documentation.indigitall.com/reference/android-sdk)
and [validation guide](https://documentation.indigitall.com/reference/sdk-integration)
describe Firebase configuration and registration of `pushToken` against a device.
Apple's
[FCM delivery path](https://firebase.google.com/docs/cloud-messaging/ios/receive-messages)
still depends on APNs, so the existing iOS token is not a portable Linux receiver.

An isolated Python probe using `firebase-messaging==0.4.5` successfully:

1. Obtained an FCM registration using the public official web client's Firebase
   configuration. Its Firebase project and sender match the installed native app.
2. Persisted independent receiver credentials in private temporary storage.
3. Authenticated a Google MCS connection with the library's Chromium/Linux profile,
   then stopped cleanly.

The initial probe ran on macOS. Repeating it in an ephemeral local Linux
container (`python:3.14.6-slim`, image digest
`sha256:7bec7ddcddeff7975d6ba9b4be7dd6f6b2f55e7491539145e2978f7f97ce9144`)
also registered/reused the receiver and authenticated MCS, then stopped cleanly.
These initial transport-only runs did not by themselves prove account binding
or delivery. The actual HA runtime/dependency compatibility and an exhaustive
Android app comparison remain untested. The receiver uses public client
configuration, not a Firebase service-account/server credential.

After the owner's specific authorization, a separate Indigitall device was
created (HTTP 201), and registering the FCM token returned HTTP 200 with
`platform: android`. An initial request without the application header returned
401. The official `android-commons` 7.1.0 source from Maven Central confirms
`x-app-android` carries the package name; the package is published in the official
My Verisure Google Play listing. Adding that observed SDK contract resolved the
registration rejection. This is a hybrid Linux/FCM feasibility probe, not a
captured Android app flow. No existing device or token was replaced. Account
binding requires separate device authentication. The owner subsequently authorized
that binding and completed SMS verification. The probe's first completion attempt
raised a device-authorization error; a single later login was accepted without
another SMS and persisted access/refresh tokens. The exact failing response was
not captured, so this does not establish a production authentication fix.

Two isolated one-camera requests then produced three fresh images each, but no
MCS data stanza arrived within either 75-second observation window. The second
request followed a specifically authorized update of the SDK `externalCode`,
accepted with HTTP 200. A read-only SDK device inspection returned enabled/Android;
it exposes no delivery-error detail. These failed delivery observations must not
be represented as a working push integration.

A subsequent comparison identified another material mismatch: the native login's
64-character `idDevice` exactly matches the APNs `pushToken` in the SDK capture.
The probe had used a generated random device identifier at login while registering
FCM only in Indigitall. The official embedded client recognizes `OWA_10` and
`OWI_10` client profiles. With explicit owner permission, the receiver's FCM token
was sent as `idDevice` with `OWA_10`, retaining the probe UUID and separate storage.
Verisure accepted that login without another SMS; the returned token confirmed
the Android profile. The next photo request delivered a real FCM event to Linux
in 19.104 seconds.

The first event was encrypted with `aesgcm`. Its Crypto-Key header contained
both `p256ecdsa` and `dh`; the library's fixed prefix removal attempted to decode
the entire combined value as base64 and failed. Parsing named parameters and
normalizing base64url padding decrypted the preserved event locally. Its sender,
installation, signal, camera and freshness were verified against authoritative
thumbnail/photo reads, which returned three images.

The [offline experimental decoder/check](../../experiments/linux_push/README.md)
preserves four synthetic encrypted round trips that reproduced the old failure and validated
parameter order, quoted/whitespace forms and padding handling. The corrected
Linux listener then received and automatically decoded a second real event in
18.582 seconds. The probe used its received `idSignal` and authoritative signal
type 16 to retrieve/commit three fresh images by 20.156 seconds, with one initial
status read and no fallback status read. The event used `request: INF`, `type: 0`
and an empty `signalType`; display text alone was not treated as confirmation.

At that prototype stage, the current Android app flow had not been captured;
the experiment reused an approved native `externalCode` and left HA unchanged.
Both test listeners were stopped. The later direct-registration result below
removed that account-identifier dependency, and the installed HA entry now uses
OWA. Complete current Android app parity remains unverified.

## Implemented boundary and lifecycle

FCM is an outbound persistent connection. Each enabled entry owns an independent
Google receiver and binds its token through the normal authorized Verisure device
flow. It must not
overwrite the native app's or a phone's SDK device ID or push token.

Keep the provider registration adapter separate from the domain event consumer.
The adapter must validate payload shape, installation and device ownership, and
deduplicate delivery IDs before publishing an internal event. Notifications are
hints to fetch authoritative photo/state data; they never issue alarm commands.
Correlate photo completion to the selected camera and pending request. Do not
show an old photo as the result of a new request.

Prepare and start the receiver before native authentication so its persisted
token can be bound during login. Hints have no effect without an active photo
request. Persist credentials privately and cancel/await all tasks on unload. Reconnect with bounded backoff,
reuse the identity after restarts, and retain a conservative polling fallback
when delivery is unavailable. Unknown payloads and duplicate notifications must
not generate repeated API requests. No public inbound port is required by this
transport.

The library's current decoder cannot be adopted unchanged for the observed
header. The maintained adapter and synthetic tests cover header forms, malformed input,
credential reuse, sender filtering and task ownership. The installed integration
pins `firebase-messaging==0.4.5`; actual HA runtime validation is recorded below.

## Direct registration and HA implementation

A fresh independent Google FCM token, never registered with Indigitall, was
bound as `idDevice` through the same Android login. It received the selected
camera event in 18.882 seconds and committed three matching fresh images by
20.147 seconds. This resolves the earlier cold-start uncertainty: production
uses Google registration and native Verisure authentication, without the captured
`externalCode`, an Indigitall app key or a new Indigitall registration request.

The integration now implements an optional entry-owned receiver. The shared
native profile selects OWA consistently for login, renewal, SMS and data calls;
a token change retains the entry UUID. An authenticated decoder handles combined
headers, and a bounded broker only wakes an existing photo request. Thumbnail
camera/signal/timestamp checks precede exact image retrieval. Missing hints retain
the existing status polling interval and reference. Private state is written
atomically with mode 0600. Entry unload drains SDK tasks and cancels pending waits.

The implementation passed the full 862-test pinned HA suite (89% aggregate
coverage), mypy, critical lint, architecture, dependency and distribution checks.
The actual HA 2026.11.2 entry committed three images through push in 21.13 seconds.
With the receiver disabled, an accepted request completed through three status
reads in 45.07 seconds. The initial Google registration and an earlier camera
request were rejected; spaced retries succeeded. Their exact causes are unknown.
The corrected receiver reused its durable credentials after restart and completed
a further push capture in 23.55 seconds. All 143 installed source hashes and
registry identities were verified; temporary logging was restored to warning. See the separate
[HA receipt](../validation/2026-11-23-ha-push.json); isolated probe timings remain
labeled as prototype observations.

## Verification record and remaining scope

- Register a separate provider device and confirm the returned ID/platform/token
  association without modifying an existing device.
- Complete normal account/device verification if required, without replacing the
  working HA config entry or invalidating its session.
- Receive one real photo-ready notification in the Python process; record only
  sanitized schema, correlation and timing. A successful token PUT is insufficient.
- Retrieve the selected camera's fresh image once, and compare completion time
  and API count against the native app and the current polling fallback.
- Repeat transport startup/reconnect on the actual Linux HA runtime, including
  dependency compatibility, unload, cancellation and restart persistence.
- Verify missed, duplicate, malformed, foreign-installation and out-of-order events
  with synthetic tests; preserve backoff and privacy.
- Disabling stops only the integration listener and retains its private identity
  for reuse; it does not unregister phones or remove provider devices. Broader
  camera-family and current Android app comparisons remain separate work.

The installed option retains polling as its fallback. Private captures,
receiver keys/tokens and household images are not repository fixtures.

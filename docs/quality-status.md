# Quality status

Updated: 2026-11-23

## Current local evidence

- Home Assistant Core: `2026.8.1`
- Python: `3.14.6`
- Home Assistant test plugin: `pytest-homeassistant-custom-component==0.13.355`
- Full Home Assistant/Core suite: **1,358 passed** in the pinned validation environment
- Measured coverage: **82% combined production line/branch coverage** (`9,346` statements; `1,492` missed); the 10 notification modules enforce **100% executable lines and branches**
- Mypy: no issues in `298` source files
- Critical Flake8 gate: passing
- Architecture guard: passing
- Distribution validation: passing

These metrics describe local verification. GitHub Actions and HACS results are
reported separately on each pull request; they do not imply a published release.
The Python CI job uses Ubuntu 24.04 for the pinned Python 3.14.4 build. The moving
`ubuntu-latest` image became Ubuntu 26.04, where that Python patch has no official
setup-python distribution; the initial run stopped before dependency installation.
The target requirements also include `firebase-messaging==0.4.5`, matching the
integration manifest so a clean CI environment can import the optional receiver.

## Full lint policy

`make lint` remains intentionally available and reports the complete Flake8
baseline. The remaining findings are primarily historical whitespace and line
length debt (`W293` and `E501`); they are not hidden by a global ignore. The CI
gate blocks syntax/import-safety findings through `make lint-critical`, while
other historical style findings remain visible.

## Evidence boundaries

The [notification audit](technical/notification-audit-and-design.md) originally reproduced
state-order, HTTP-admission, canceled-write and cached-crypto defects on develop.
They now have passing correction regressions. The implementation adds typed reported
and confirmed events, read-only scheduling, transactional binding and durable replay.
Real HA platform tests cover event.received, restore, context, reconnect, unload,
multiple entries, options and diagnostics. The [implementation receipt](validation/2026-11-23-notification-implementation.json)
separates these synthetic guarantees from household delivery evidence. General
non-photo delivery remains unverified.

Coverage now uses an explicit .coveragerc with branch measurement and production
files only; tests are excluded from its denominator. The historical 90% metric
is not directly comparable. CI fails if any executable line or branch in the ten
notification modules is missing coverage.

Automated tests use synthetic data and make no provider calls. Separately, the
owner explicitly authorized household validation on HA Core `2026.11.2` with
native My Verisure `10.192.1` as the protocol reference. That session established
device/SMS verification, token renewal, installation/service/device projection,
exterior and partial-night commands, supplementary perimeter, completion-state
publication and restoration to fully disarmed.

The installed correction was exercised after actual token expiry: Night plus
perimeter took about 4.0 seconds including renewal; the following disarm took
about 3.9 seconds including HA-side completion. Individual observations do not
establish an SLA or exhaustive equivalence with the official application.

Total/away and partial-day modes were not exercised live. Home is confirmed as
exterior-only. A selected-camera HA refresh produced and displayed three fresh
images in 24.88 seconds; native capture was also observed separately. Broader
camera-family parity is not established. The optional production FCM receiver is
now installed on the existing HA entry. A selected fresh capture committed three
images in 21.13 seconds using one initial status read and a verified push hint.
With the receiver disabled, a later accepted capture committed three images in
45.07 seconds with unchanged 20-second polling. One earlier request was rejected;
a spaced retry succeeded, but its exact provider cause was not retained.
The UI now uses recognized, translated Home Assistant camera errors instead of
exposing provider errors as an unknown failure. After a full restart, the same FCM token and all entity identities were retained;
a further capture completed through push in 23.55 seconds.
See the [installed receipt](validation/2026-11-23-ha-push.json) and
[push baseline](../specs/linux-push-photo-completion.md).
The follow-up public Firebase configuration correction has 20 additional synthetic
regressions and a two-GET unauthenticated production-metadata comparison. It is now installed with the notification implementation; the older runtime
timings above describe the preceding build. A new selected-camera capture committed
three images in **23.22 seconds**, publishing one `photo_reported` and one correlated
`photo_ready` with `verification=image_commit`. The receiver was bound/connected,
with zero additional duplicate photo reads and no current provider cooldown.
The same 20 original entity identities, native UUID and FCM token survived restart
and entry reload; restored display retained the original photo timestamp.
No alarm commands were sent by this agent during this iteration. See the [security review](technical/firebase-client-configuration.md).
Camera refresh serialization and failure propagation are covered by new regressions.
Alarm command serialization and stale snapshot publication are now covered by
shared-installation operation locks, generations and cancellation regressions.
Broader compound-command physical recovery and freshness UX remain evidence limits. See the [dated report](validation/2026-11-22-live-verisure.md)
and [specification catalog](../specs/README.md).

Credentials, OTPs, tokens, private captures and HA storage must not be committed.
Private source/session and registry rollback archives remain on the HA host.
The isolated container lifecycle checklist was not executed in this iteration.

## Source of truth

The executable gates are defined in `Makefile` and `.github/workflows/validate.yml`.
The current execution record is
`docs/superpowers/plans/2026-11-22-ha-push-installation.md`, with the follow-up
`docs/superpowers/plans/2026-11-23-public-firebase-config.md`, followed by
`docs/superpowers/plans/2026-11-23-notification-implementation.md`.

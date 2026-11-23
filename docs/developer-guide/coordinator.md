# Coordinator

`MyVerisureDataUpdateCoordinator` owns one composition root per config entry and
is stored in `entry.runtime_data`. Core application modules do not import HA.

## Routine refresh

The interval uses options, then config-entry data, then the default of 10 minutes.
An options change reloads the entry through `update_listener`; unload stops
scheduled coordinator work and its optional receiver.

1. Load the persisted session and native device profile before accepting cached
   authentication. Prepare optional push registration before native login.
2. Authenticate through the session policy, reusing or renewing the session and
   respecting provider blocking/backoff.
3. `InstallationSnapshotService` loads installation services/capabilities before
   reading alarm status with that context.
4. Reject a session change during the read, then publish/persist a redacted
   snapshot through `CoordinatorRefreshEffects` and `CoordinatorSnapshotStore`.
5. Bootstrap camera placeholders without treating them as fresh captures.

Authentication failures enter HA reauthentication. Provider blocking raises a
persistent notification and can fall back to an existing snapshot. Other
failures retain their established application/HA classification; cached data is
not evidence of a new successful provider read.

## Commands and camera requests

Alarm commands authenticate and refresh installation permissions when their
session binding changes or capability JWT expires. Confirmed completion updates
the panel directly; a failed or unconfirmed command must not claim success.
The supplementary exterior option applies to the configured interior modes.
Home remains exterior-only; Night is interior partial night.

An entry-local lock rejects overlapping camera refreshes. The optional camera
selector is resolved against that entry's registry before sending a request.
FCM can wake the existing request only after installation/time checks; exact
thumbnail signal, camera and freshness checks precede image commit. Without a
usable hint, polling keeps the same reference and 20-second interval.

## Receiver lifecycle and logging

`HomeAssistantPush` and `PushReceiver` own registration, private persistence and
listener tasks. Valid stored credentials are reused directly on startup and
transport reconnect. An actual MCS login rejection requests registration recovery.
Unload cancels and awaits SDK tasks, including SDK stop's early-return case.

Use safe INFO completion/connection logs during a controlled diagnostic session,
then restore normal levels. SDK verbose payload logging stays disabled. Never
publish receiver keys, session tokens, raw notifications or private image paths.

See the [push specification](../../specs/linux-push-photo-completion.md),
[session contract](../../specs/native-authentication-and-session-lifecycle.md)
and [validation evidence](../quality-status.md).

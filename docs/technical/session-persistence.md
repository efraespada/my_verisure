# Session persistence

Session manager persists secrets needed to rebuild authenticated GraphQL headers without interactive login each poll.

Paths are entry scoped under HA's `.storage/my_verisure_<entry_id>/data/`, derived
from the injected FileManager. `session.json` holds the token pair and credentials;
device identifiers are stored within the same entry-owned root. Refer to
[`coordinator.py`](../../custom_components/my_verisure/coordinator.py).

Successful native login/renewal persists atomically before publishing the new
session. A failed write restores the prior disk and memory state. On expiry, try
the stored native refresh token; request interactive device verification only
when the provider requires it. Background polling does not intentionally start
a new password/SMS flow on every update.

Installation capabilities may be scoped to the access session. Commands refresh
that context on session change or capability expiry and reject a concurrent
session change before mutation. A persisted token pair alone is insufficient
evidence that cached installation permissions are current.

## Guidance

- Treat stored JSON like credentials — **exclude from public backups** or encrypt backups at rest.  
- Update credentials through reauthentication to preserve the existing entry and
  entity identities; do not remove/recreate an entry as a routine refresh step.

See the [authentication contract](../../specs/native-authentication-and-session-lifecycle.md)
and [controlled validation report](../validation/2026-11-22-live-verisure.md).

## Receiver identity

`push_credentials.json` stores the receiver's keys, registration and bounded
delivery history with atomic replacement and mode 0600. The device file persists
the notification token and protocol profile without changing the UUID. Neither
file belongs in a public issue or PR.

Valid credentials resume MCS directly; a transient check-in must not replace a
working receiver. Only an actual MCS authentication rejection requests registration
recovery. Transport failures retain bounded reconnect delays and camera polling.
Entry unload drains tasks; reauthentication and reload preserve registry identity.

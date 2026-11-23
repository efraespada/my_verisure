# Data flow

## Polling and selective reads

1. HA invokes the coordinator's configured update path. Authentication selects a
   valid session or attempts native renewal through the entry-owned manager.
2. The snapshot service reads alarm and installation data through application
   use cases and ports. Provider admission is shared across entries for the origin.
3. Before publication, the coordinator rechecks the session binding and the
   shared installation generation/operation lock. An obsolete response cannot
   overwrite a newer command or snapshot.
4. HA receives the runtime snapshot; a bounded, allowlisted projection is saved
   separately for offline fallback. Persistence workers are owned/drained so
   canceled older writes do not overtake newer ones.
5. Entity platforms map the current runtime snapshot into HA states. A cached
   snapshot retains its original timestamp and does not prove live freshness.

Optional notification hints schedule selective read-only verification rather
than unconditional full refreshes. The notification runtime checks installation
scope, freshness, permissions and operation generations before publishing safe
reported/verified events. See [notification automation](../automation-notifications.md).

## Command path

1. An explicitly invoked service/UI action selects the entry coordinator.
2. The coordinator serializes the physical installation's complete operation,
   authenticates and validates installation capabilities for that session.
3. Application workflow executes the requested mutation and waits for the
   provider's bounded completion response. Supplementary perimeter is a second
   step only when its option is enabled and the interior step succeeded.
4. A recognized completion state can publish directly and produce a verified
   local result; it does not require waiting for routine polling. Unknown,
   rejected and partial results retain their failure semantics.

Notifications never invoke these commands. Offline cache is not command
confirmation. See [alarm contract](../../specs/alarm-modes-and-confirmation.md).

## Persistence boundary

`CoordinatorSnapshotStore` projects data through `persistable_snapshot()` before
saving or reading coordinator fallback JSON. It retains normalized alarm-zone
values, safe service flags and the observation timestamp, rather than dumping
raw provider responses, account/installation IDs, capability JWTs, device
metadata or addresses. This projection is separate from private credential/
session storage and camera files. Session files still require secret handling.
See [session persistence](../technical/session-persistence.md).

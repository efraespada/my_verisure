# Session management

Session state is owned by an entry-scoped [`SessionManager`](../../custom_components/my_verisure/core/session_manager.py).
The `CompositionRoot` creates one manager per Home Assistant config entry and
injects it into all API clients and application services. Production code must
not obtain session state through a process-global accessor.

## Responsibilities

- Store username/password/hash/refresh tokens in the entry-owned manager.
- Persist session data under the Home Assistant storage path assigned to the
  config entry.
- Validate expiry and service-block cooldown state.
- Provide credentials to the entry-scoped GraphQL clients.

## Interaction flow

1. Config flow supplies credentials to the entry's composition root.
2. GraphQL clients read tokens from the injected `SessionManager`.
3. The coordinator performs login, reauthentication, and refresh through the
   same entry-owned manager.
4. Unloading one config entry releases its graph without changing another
   entry's session, files, or clients.

For security guidance, treat session files as secrets and restrict backups.

See also [session-persistence.md](../technical/session-persistence.md).

# Diagram — authentication and native refresh

```mermaid
flowchart TD
  start[Entry-owned async_login transaction]
  blocked{Provider cooldown active?}
  valid{Current session valid?}
  refreshable{Refresh credentials available?}
  refresh[SessionManager.ensure_authenticated]
  native[Native refresh or required device login/SMS]
  persisted{Accepted tokens persisted?}
  done[Return authenticated]
  unavailable[Return unavailable or classified authentication error]
  snapshot[Read path may use a safe timestamped cache]

  start --> blocked
  blocked -->|yes| unavailable
  blocked -->|no| valid
  valid -->|yes| done
  valid -->|no| refreshable
  refreshable -->|no| unavailable
  refreshable -->|yes| refresh
  refresh --> native
  native --> persisted
  persisted -->|yes| done
  persisted -->|no, restore prior state| unavailable
  unavailable --> snapshot
```

The login lock serializes the entry's authentication transaction. Device-bound
SMS is guided through config/reauth flow when required; a background refresh
cannot prompt interactively. Authentication is published only after persistence.
Push binding commits only with the accepted session. Cache fallback belongs to
reads and never proves completion of a physical alarm command.
See [authentication contract](../../../specs/native-authentication-and-session-lifecycle.md).

# Authentication

Flow outline:

1. **Username/password** submitted via config flow.  
2. `AuthUseCase.login` obtains tokens via GraphQL.  
3. **OTP path** — provider requires device verification → select the exact offered phone identifier (including zero) → send SMS → verify the pending device-bound challenge → perform native login again.
4. A strictly accepted native response supplies access and refresh tokens. Publish
   authentication only after transactional persistence succeeds.
5. Use the native refresh-token flow when access expires. Preserve stable device
   identifiers; login/SMS and embedded data calls use their respective observed
   native/web header profiles.
6. Data calls attach the access hash in HTTP headers. Alarm commands additionally
   require installation permissions bound to that same session.

See diagrams [authentication-flow.md](../architecture/diagrams/authentication-flow.md).

## Failure modes

- Invalid credentials → `MyVerisureAuthenticationError`.  
- OTP mismatch → `MyVerisureOTPError`.  
- Vendor temporary lockouts → `MyVerisureServiceBlockedError`.
- Missing/expired/replayed SMS challenge → stop; do not reuse authorization from
  a different login/device. Incomplete or unknown login success shapes fail closed.
- Persistence failure → restore previous memory/disk state; do not advertise an
  unpersisted session as authenticated.

The maintained detailed contract and current evidence are in the
[authentication specification](../../specs/native-authentication-and-session-lifecycle.md).

## Optional FCM profile

The default native profile is OWI. Enabling immediate photo updates registers an
independent receiver and binds its token as `idDevice` with OWA, retaining the
entry UUID. Authentication, verification and data clients share that profile.
A profile mismatch invalidates the candidate in-memory session before reuse;
accepted authentication still follows the existing persistence transaction.

Stored receiver credentials are reused across restart. Disabling push stops the
listener but retains the verified OWA profile and usable polling session. See the
[push baseline](../../specs/linux-push-photo-completion.md) and
[installed evidence](../validation/2026-11-23-ha-push.json).

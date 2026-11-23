# Home Assistant push installation implementation plan

> **For agentic workers:** Execute inline with the executing-plans workflow. The owner explicitly requested implementation, installation and controlled validation in this session; no execution handoff is needed.

**Goal:** Install entry-owned Linux FCM photo completion in HA, retaining conservative polling and all existing entity IDs.

**Architecture:** A graph-owned native profile keeps authentication and data clients consistent. An entry-owned receiver writes private credentials atomically and feeds a bounded photo-hint broker; only an active camera request can consume a hint, and authoritative thumbnail/photo validation precedes completion. The existing coordinator interval, camera lock, authentication/capability binding and 403 cooldown remain in effect.

**Tech Stack:** HA/Python, aiohttp, firebase-messaging 0.4.5, authenticated aesgcm decoder, pytest and the existing pinned HA validation environment.

## Files and responsibilities

| Files | Responsibility |
|---|---|
| `core/api/native_profile.py`, `device_manager.py`, `base_client.py`, `auth_client.py`, DI providers | entry-scoped OWI/OWA profile and notification token; preserve UUID |
| `core/application/photo_notifications.py` | bounded pending request, timestamp/installation validation and deduplication |
| `core/api/push_decoder.py`, `push_receiver.py`, `push_storage.py` | maintained decoder adapter, Google receiver, private state and clean shutdown |
| `camera_client.py`, result DTO/domain mapper, camera repository port/adapter and image use case | exact signal retrieval, authoritative camera validation, push wait and polling fallback |
| `coordinator.py`, `integration.py`, `config_flow.py`, `const.py`, translations and manifest | opt-in lifecycle, preparation before authentication, diagnostics and fallback |
| new core/HA tests, specification and validation report | synthetic regression coverage and controlled installed evidence |

## Task 1: Remove the cold-start registration uncertainty

- [x] Register an independent Google FCM receiver, without registering its token in Indigitall. Retain the probe UUID, use its token as `idDevice` with OWA_10, and request one camera after the previous test is well spaced.
- [x] Require an encrypted event and an authoritative matching image set. If direct delivery works, omit Indigitall/account-identifier capture from production; otherwise resolve the supported registration input before enabling the feature.
- [x] Check dependency resolution against constraints captured from the working HA test environment. Run `pip check`; do not force newer cryptography/protobuf into HA.

## Task 2: Profile, private state and broker regressions before implementation

- [x] Add failing tests for independent profiles, a stable UUID across token changes, OWA login/refresh/session headers and legacy OWI defaults.
- [x] Define a shared profile context with an iOS default. Device loading selects its stored profile; the coordinator loads device state before checking cached authentication. Authentication clients use that context for login/renewal/OTP as well as ordinary data headers.

```python
@dataclass(frozen=True)
class NativeProfile:
    callby: str
    session_id: str
    os_version: str
```

- [x] Add a private atomic JSON writer using `mkstemp`, mode 0600, `os.replace` and executor I/O. Verify a failed write preserves prior bytes and that credentials cannot escape the entry-owned directory.
- [x] Add a broker that allows only one pending request per entry, ignores foreign/stale/malformed/duplicate hints, caps retained delivery IDs and exposes no public payload.

```python
def begin(installation_id: str, started_at: float) -> None: ...
def receive(payload: dict, persistent_id: str) -> None: ...
async def wait(timeout: float) -> str | None: ...
def finish() -> None: ...
```

- [x] Run the new focused tests with `TMPDIR=/private/tmp` and the pinned HA interpreter; verify the failures are meaningful, then implement the profile/store/broker and require passing results.

## Task 3: Receiver and camera completion

- [x] Promote the live-tested pure decoder to the API adapter and test encrypted header ordering, quoted parameters, missing padding and malformed messages with synthetic keys.
- [x] Implement credential reuse and update persistence, callback isolation, bounded reconnection, startup timeout and stop/await behavior. A callback never issues alarm operations or refreshes all installation data.
- [x] Register a pending photo before `RequestImages`, perform the existing initial status read, then wait for push within each existing polling interval. A missing/disconnected receiver uses the same bounded 20-second status schedule. Always clear pending state on success, failure or cancellation.
- [x] Validate a candidate's authoritative thumbnail against the requested camera, installation and fresh hint timestamp. Ignore a rejected candidate and continue the same request reference; never issue another photo mutation as fallback.
- [x] Carry an optional signal ID through the request result/repository into retrieval. A verified push completion skips the legacy three-second delay and retrieves/commits its exact photo signal. Preserve legacy calls when no signal is supplied.
- [x] Test success without a second status call, timeout/disconnect fallback, a wrong camera, replay, cancellation, provider 403 and unchanged attempt/interval budgets. Run focused core tests before HA wiring.

## Task 4: HA opt-in and lifecycle

- [x] Add `push_enabled`, default false for existing entries, to options and translations. Manifest adds only firebase-messaging 0.4.5; retain polling classification while routine alarm reads still poll.
- [x] Prepare the receiver/token before initial authentication when enabled, preserving the original entry/UUID/registries. A profile/token mismatch invalidates only the candidate in-memory session so normal authentication obtains matching tokens. Use the existing SMS reauth flow if requested.
- [x] Start/stop the receiver with entry setup/unload, including setup failure cleanup. Receiver startup failure logs a safe stage and leaves polling usable; an already migrated profile remains consistent if the listener is temporarily unavailable.
- [x] Verify lifecycle with fake receiver/no provider, two entries, failed startup, authentication failure, unload/reload and callback exceptions. Add sanitized connection diagnostics and keep credentials out of entity attributes and diagnostics.

## Task 5: Release gates, installation and live checks

- [x] Run the complete pinned HA suite, mypy, critical lint, architecture guard, dependency/distribution checks and whitespace validation. Review the final diff and scan for actual private values.
- [x] Build a production-only archive, include the established legacy radio polling file, retain the current installed source/session/registry rollbacks, verify SHA-256 in HA, check configuration and restart.
- [x] Enable push on the existing entry and verify a Google listening state, OWA authentication and synthetic renewal, 20 preserved entities and unchanged registry IDs. Request a new SMS only after a genuine challenge.
- [x] Request one selected camera, require push receipt plus exact fresh image commit, and record latency/provider calls. After spacing the next request, deliberately stop the receiver through the supported option/lifecycle and verify the same image workflow completes through polling.
- [x] Restore push, verify restart/credential reuse and safe logs. Alarm total/away is forbidden; camera tests require no alarm commands.
- [x] Update the SDD/report with actual installed results, preserve only current rollback/evidence and remove owned uploads/caches. Stop only experimental listeners, leaving the installed HA receiver running if healthy.

## Acceptance

The installed HA entry receives real photo completion and falls back without new mutations or a request burst when push is unavailable. Session/profile state survives restart, entry unload owns every task, the old registry identity is preserved, and no sensitive payload is logged. Ordinary ten-minute alarm polling remains enabled. No alarm total command is issued.

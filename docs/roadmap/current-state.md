# Current state assessment

## Strengths

- Modern **GraphQL** architecture with layered repositories/use cases.  
- Comprehensive **pytest** coverage around embedded core (`custom_components/my_verisure/core/tests/unit`).  
- **Coordinator** consolidates polling + imperative alarm commands.  
- **Config flow** covers OTP branches + installation selection + options for polling/perimeter behavior.  
- **CI**: HACS validation workflow ([`.github/workflows/validate.yml`](../../.github/workflows/validate.yml)).

## Implementation realities

- Each config entry owns its coordinator through `runtime_data` and its isolated
  composition root. Domain-level state is limited to shared service registration.
- Logging verbosity — frequent **warning** level traces during normal operation.  
- Cameras serve complete committed filesystem snapshots. Optional FCM verifies
  the exact signal/camera/time before retrieval and retains polling fallback.
- Registry identity, native session lifecycle and actual selected-camera
  push/polling/restart behavior have evidence in the [capability catalog](../../specs/CATALOG.md).
- Broader camera coverage, physical compound-command recovery and
  stale-image presentation remain separate acceptance boundaries.

## Evaluated future app coverage

The [global web/native audit](../technical/2026-11-24-app-capability-audit.md)
evaluates all recovered operation families, including access/users, panel/sensor
settings, provider routines, activity/inbox, media, locks, health, administration
and native personal services. The [catalog](../../specs/CATALOG.md) separates five
existing baselines from eleven Draft SDDs; proposed functions are not installed.

Recommended order: shared permissions/operation lifecycle, bounded read-only
views, confirmed configuration/access changes, schedules, then hardware-specific
media/locks and protected personal/account flows. Native SDK transport, mailbox
access, telemetry sources and panel-specific write contracts remain explicit
readiness gates. Purchases, consent and emergency actuation retain official flows.

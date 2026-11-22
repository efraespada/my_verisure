# Changelog

## Unreleased

### Added

- Optional entry-owned FCM receiver for photo completion, with private atomic
  credential storage, authenticated decoding, bounded recovery and safe diagnostics.
- Photo signal, camera and timestamp validation before committing fresh images;
  the existing 20-second status polling remains the fallback.
- An optional camera selector for the refresh service, preserving the all-camera
  button and default service behavior.
- Four capability specifications, a traceability catalog and sanitized records
  separating synthetic checks, native observations and actual HA validation.

### Fixed

- Native login and refresh profiles, device-bound SMS handling including phone
  identifier zero, nullable authorization responses and transactional persistence.
- Session-bound installation permissions and confirmed alarm states, without
  redundant radio checks after successful commands. Home remains exterior-only;
  supplementary perimeter applies to the configured interior modes.
- Camera base initialization, nullable device metadata and stable per-entry
  identities. Unambiguous registry migration retains existing entities and links.
- Overlapping photo refreshes, image persistence failure propagation and safe
  Home Assistant action errors.
- Reuse of stored FCM credentials after restart, avoiding unnecessary registration
  when a transient Google check-in fails.

### Validation scope

The pinned automated target is HA Core 2026.8.1; live validation used HA Core
2026.11.2. A selected camera completed through FCM, disabled-receiver polling and
FCM again after restart. Interior total and partial day were not tested live.
See [quality status](docs/quality-status.md), [the catalog](specs/CATALOG.md) and
[the installed receipt](docs/validation/2026-11-23-ha-push.json).

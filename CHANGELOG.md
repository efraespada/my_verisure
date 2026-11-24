# Changelog

## [Unreleased]

### Documentation

- Evaluate official Spanish web 3.8.0 and native WebView 10.192.1 functionality
  for future HA expansion, including native-only surfaces and SDK limitations.
- Add eleven Draft SDDs with capability/permission gates, Clean Architecture design,
  acceptance, recovery, privacy and future test budgets. Catalog all 263 recovered
  unique GraphQL operation names (278 textual variants) and 152 native commands
  with source identities and decisions.
- Specify complete physical-device registration, independent remote/local names,
  sensor day/night combinations, chime prerequisites, manual Wi-Fi and screen-level
  coverage for comfort, visits, routines and battery workflows.
  This documentation does not add runtime features or change the installed version.

## [1.1.0] - 2026-11-23

### Added

- Optional entry-owned FCM receiver for photo completion, with private atomic
  credential storage, authenticated decoding, bounded recovery and safe diagnostics.
- Photo signal, camera and timestamp validation before committing fresh images;
  the existing 20-second status polling remains the fallback.
- An optional camera selector for the refresh service, preserving the all-camera
  button and default service behavior.
- Capability specifications, a traceability catalog and sanitized records
  separating synthetic checks, native observations and actual HA validation.
- Typed notice and verified-result event entities, optional advanced event bus,
  selective state synchronization and external-photo imports with independent
  options, safe automation examples and receiver/category diagnostics.
- Notification contracts and architecture decisions documenting delivery limits,
  dependency boundaries and independently confirmed outcomes.

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
- Automatic discovery of public Firebase client configuration for new registration,
  removing the provider API-key literal from current source while preserving
  cached startup and polling fallback. Alert provenance and limits are documented.
- Current-HA option-form serialization, strict scan-interval validation and
  redundant installation reads during routine polling.
- Reauthentication after changing login credentials, recovery from malformed
  persisted sessions and bounded JWT metadata validation.
- Bounded JPEG/PNG validation and metadata removal before photo persistence,
  rejection of malformed/animated images and stale photo-completion markers.
- Propagation of status-action failures and deterministic CLI state isolation,
  non-interactive behavior and exit codes.

### Validation scope

The pinned automated and observed household target is HA Core 2026.11.2 on
Python 3.14. The pre-release audit passed 1,707 tests; integration-wide coverage
was 85.20% of executable lines and 75.98% of branches, with enforced 100% coverage
for the selected critical modules. This is not a claim of exhaustive provider
or device behavior.

Prior live validation completed a selected camera through FCM, disabled-receiver
polling and FCM again after restart. The current-runtime installation also
verified a scheduled poll, automatic session renewal, connected push transport
and preservation of all 28 existing entity identities and options. Interior total
and partial day were not tested live; notification-category delivery remains
limited to the observed examples.
See [quality status](docs/quality-status.md), [the catalog](specs/CATALOG.md) and
[the installed receipt](docs/validation/2026-11-23-ha-push.json).

[1.1.0]: https://github.com/efraespada/my_verisure/releases/tag/v1.1.0

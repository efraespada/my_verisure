# Capability catalog

Source: [catalog.json](catalog.json), schema version 1. It contains five as-built baselines and ten Draft future capabilities. Baselines
do not claim complete household delivery coverage. Drafts do not add runtime
features or an installed Copilot workflow.

| ID | Specification | Status | Verified | Principal remaining evidence |
|---|---|---|---|---|
| `native-authentication` | [Native authentication and session lifecycle](native-authentication-and-session-lifecycle.md) | As-built baseline | 2026-11-23 | future profile compatibility and maintainer review |
| `alarm-commands-and-state` | [Alarm modes and provider confirmation](alarm-modes-and-confirmation.md) | As-built baseline | 2026-11-23 | broader compound recovery, owner-reserved total test |
| `installation-and-camera-data` | [Installation data, cameras and identity](installation-cameras-and-entity-identity.md) | As-built baseline | 2026-11-23 | broader camera coverage and freshness UX |
| `linux-push-photo-completion` | [Linux push reception and photo completion](linux-push-photo-completion.md) | As-built baseline | 2026-11-23 | broader camera/Android coverage; rejection causes |
| `notification-observability-and-automation` | [Notification observability and automation](notification-observability-and-automation.md) | As-built baseline | 2026-11-23 | non-photo delivery/entitlement; controlled rollout evidence |

See [the specification standard](README.md) for status semantics, evidence rules
and the explicit boundary before a future Copilot integration.

## Future app capabilities — Draft

The [global app audit](../docs/technical/2026-11-24-app-capability-audit.md) evaluates
web and native surfaces together. Research dates below do not claim implementation
or tests. All ten entries retain open readiness gates; code/test arrays in the JSON
are empty until the implementation exists.

| ID | Specification | Status | Research date | Principal readiness gate |
|---|---|---|---|---|
| `app-management-foundation` | [Shared management capabilities, permissions and operation lifecycle](app-management-foundation.md) | Draft | 2026-11-24 | capabilities/roles, protected authorization, resource generations and operation admission |
| `access-control-and-users` | [Llaves, mandos, usuarios y permisos](access-control-and-users.md) | Draft | 2026-11-24 | panel/role contracts, tri-state patches, tracking feature flag and partial confirmation |
| `installation-and-device-settings` | [Configuración de instalación, panel, sensores y red](installation-and-device-settings.md) | Draft | 2026-11-24 | effective panel ranges, radio confirmation, hardware flags and sensitive network flow |
| `provider-routines-and-schedules` | [Rutinas, recordatorios y calendarios del proveedor](provider-routines-and-schedules.md) | Draft | 2026-11-24 | non-idempotent state changes, timezone/DST, pet-mode semantics and legal gates |
| `activity-inbox-and-incidents` | [Actividad, buzón e incidencias](activity-inbox-and-incidents.md) | Draft | 2026-11-24 | legitimate native inbox transport, paging, privacy and incident detail contracts |
| `connected-camera-media` | [Cámaras conectadas, vídeo, galería y configuración](connected-camera-media.md) | Draft | 2026-11-24 | SDK transport, hardware, codecs, media bounds and authorization per camera family |
| `smart-lock-management` | [Cerraduras inteligentes y configuración](smart-lock-management.md) | Draft | 2026-11-24 | hardware, lock versus open semantics, timestamps and safe physical validation |
| `system-health-and-maintenance` | [Salud, entorno y mantenimiento](system-health-and-maintenance.md) | Draft | 2026-11-24 | actual environmental source, units, side-effecting DIY queries and maintenance contracts |
| `protected-account-administration` | [Administración protegida de cuenta e instalación](protected-account-administration.md) | Draft | 2026-11-24 | intent-bound high-security authorization and private HA administration UX |
| `personal-protection-and-native-services` | [Protección personal y funciones del dispositivo nativo](personal-protection-and-native-services.md) | Draft | 2026-11-24 | SDK availability, personal consent/scope and legitimate service data; no HA emergency actuation |

# Capability catalog

Source: [catalog.json](catalog.json), schema version 1. It contains as-built
baselines, not claims of complete product acceptance
or an installed Copilot workflow.

| ID | Specification | Status | Verified | Principal remaining evidence |
|---|---|---|---|---|
| `native-authentication` | [Native authentication and session lifecycle](native-authentication-and-session-lifecycle.md) | As-built baseline | 2026-11-23 | future profile compatibility and maintainer review |
| `alarm-commands-and-state` | [Alarm modes and provider confirmation](alarm-modes-and-confirmation.md) | As-built baseline | 2026-11-22 | compound/concurrent commands, owner-reserved total test |
| `installation-and-camera-data` | [Installation data, cameras and identity](installation-cameras-and-entity-identity.md) | As-built baseline | 2026-11-23 | broader camera coverage and freshness UX |
| `linux-push-photo-completion` | [Linux push reception and photo completion](linux-push-photo-completion.md) | As-built baseline | 2026-11-23 | broader camera/Android coverage; transient provider rejection causes |

See [the specification standard](README.md) for status semantics, evidence rules
and the explicit boundary before a future Copilot integration.

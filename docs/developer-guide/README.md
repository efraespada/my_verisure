# Developer guide

For contributors working on `custom_components/my_verisure` and the bundled `core/` layer.

## Sections

| Doc | Topic |
|-----|-------|
| [local-development.md](local-development.md) | **Local Home Assistant setup with DevContainer (start here!)** |
| [setup.md](setup.md) | Virtualenv, dependencies, repo layout |
| [testing.md](testing.md) | Pytest, scripts, coverage |
| [code-organization.md](code-organization.md) | Packages and responsibilities |
| [architecture.md](architecture.md) | Short overview (deep dive in [../architecture/](../architecture/)) |
| [coordinator.md](coordinator.md) | `MyVerisureDataUpdateCoordinator` |
| [config-flow.md](config-flow.md) | Config & options flows |
| [dependency-injection.md](dependency-injection.md) | Composition and dependency boundaries |
| [api-client.md](api-client.md) | GraphQL clients |
| [entity-platforms.md](entity-platforms.md) | Platforms mapping |
| [session-management.md](session-management.md) | Session manager interaction |

Conventions: follow [`home-assistant-integration.mdc`](../../.cursor/rules/home-assistant-integration.mdc) and project Python rules.

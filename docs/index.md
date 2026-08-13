# My Verisure — Documentation Hub

Custom integration for Home Assistant connecting to **Verisure / Securitas Direct** via the official GraphQL API (`customers.securitasdirect.es`). This hub links all sections of the documentation site.

## Audience quick links

| You are… | Start here |
|----------|------------|
| End user installing from HACS | [Getting started](user-guide/getting-started.md) · [Installation](user-guide/installation.md) · [Configuration](user-guide/configuration.md) |
| Automating your alarm | [Entities](user-guide/entities.md) · [Services](user-guide/services.md) · [Automations](user-guide/automations.md) |
| Debugging issues | [Troubleshooting](user-guide/troubleshooting.md) · [FAQ](user-guide/faq.md) |
| Contributor / developer | [Developer guide](developer-guide/README.md) · [Architecture](architecture/README.md) · [Technical reference](technical/README.md) |
| Planning / roadmap | [Roadmap](roadmap/README.md) |

## Documentation map

- **[User guide](user-guide/README.md)** — Install, configure, entities, services, dashboards, automations, translations, troubleshooting.
- **[Developer guide](developer-guide/README.md)** — Setup, testing, code layout, coordinator, config flow, dependency injection.
- **[Architecture](architecture/README.md)** — Layers, data flow, patterns, error handling, diagrams.
- **[API reference](api-reference/README.md)** — Entities and services catalog with parameters and examples.
- **[Examples](examples/README.md)** — YAML snippets for automations, scripts, Lovelace.
- **[Technical](technical/README.md)** — GraphQL client, auth, session persistence, models, performance.
- **[Integration](integration/README.md)** — Using My Verisure with Node-RED, voice assistants, shortcuts.
- **[Roadmap](roadmap/README.md)** — Gaps, improvements, phased plan.

## Repository facts (current implementation)

- **Domain:** `my_verisure` · **Integration type:** hub · **IoT class:** cloud_polling  
- **Home Assistant:** `2026.8.1` (Core; Python >=3.14.2)
- **API endpoint:** `https://customers.securitasdirect.es/owa-api/graphql` (see [`core/const.py`](../custom_components/my_verisure/core/const.py))  
- **Platforms:** `alarm_control_panel`, `sensor`, `binary_sensor`, `camera`, `button` (see [`integration.py`](../custom_components/my_verisure/integration.py))

## Search keywords (findability)

`my_verisure`, `Verisure`, `Securitas Direct`, `GraphQL`, `alarm_control_panel`, `arm_away`, `arm_home`, `arm_night`, `disarm`, `get_status`, `refresh_camera_images`, `HACS`, `config flow`, `OTP`, `installation_id`, `cloud polling`, `Home Assistant 2026.8.1`.

## Contributing to docs

Documentation lives under `docs/`. When changing behavior in code, update the matching section here and cross-links from [README.md](../README.md).

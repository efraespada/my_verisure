# My Verisure

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40efraespada-blue.svg)](https://github.com/efraespada)

Current release: **[1.1.0](https://github.com/efraespada/my_verisure/releases/tag/v1.1.0)** · [Release notes](CHANGELOG.md).

Custom integration for Home Assistant that connects to the Verisure / Securitas Direct GraphQL API. Control alarm modes, read detailed zone status, refresh camera snapshots, and automate via services.

## 📚 Documentation

**Full documentation** (user guide, developer guide, architecture, API reference, examples, roadmap): **[docs/index.md](docs/index.md)** · [Documentation overview](docs/README.md)

Quick links: [Installation](docs/user-guide/installation.md) · [Configuration](docs/user-guide/configuration.md) · [Entities](docs/user-guide/entities.md) · [Services](docs/user-guide/services.md) · [Troubleshooting](docs/user-guide/troubleshooting.md)

## 🚀 Features

- ✅ **Complete authentication** with 2FA (OTP via SMS)
- ✅ **Automatic session management**
- ✅ **Multiple installations** supported
- ✅ **Alarm services** (arm/disarm, status)
- ✅ **Optional FCM photo completion** with conservative polling fallback
- ✅ **Typed notification events**, independently verified results and receiver diagnostics
- ✅ **Stable per-entry identities** preserving existing entities and automations
- ✅ **Modern GraphQL API** (doesn't use obsolete `vsure` library)

## 📋 Requirements

- Home Assistant 2026.11.2 (Core; Python >=3.14.2)
- Verisure/Securitas Direct account
- DNI/NIE and account password

## 🛠️ Installation

### Option 1: HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom integration in HACS
3. Search for "My Verisure" in the HACS store
4. Click "Download"
5. Restart Home Assistant
6. Go to **Settings** > **Devices & Services** > **Integrations**
7. Search for "My Verisure" and configure it

### Option 2: Manual installation

1. Download this repository
2. Copy `custom_components/my_verisure` to `<config_dir>/custom_components/my_verisure`
3. Restart Home Assistant
4. Configure the integration from the interface

## ⚙️ Configuration

1. Go to **Settings** > **Devices & Services** > **Integrations**
2. Search for "My Verisure" and click "Configure"
3. Enter your **DNI/NIE** (without hyphens)
4. Enter your **password**
5. Select the **phone** to receive the OTP code
6. Enter the **OTP code** you receive via SMS
7. Select the installation to configure. SMS verification is requested only when the provider requires it.

In the integration options, enable **Immediate photo updates** to use FCM.
The existing device UUID and entities are retained; another SMS may be required.
Photo status polling remains available every 20 seconds if no usable event arrives.
Routine alarm polling keeps the configured interval, which defaults to 10 minutes.
Disabling immediate updates keeps a usable polling integration and its verified profile.

The **Verisure notices** and **Verified results** event entities provide a safe
automation interface. Selective alarm/incident reads, external photo updates and
the advanced event bus are separate opt-in options. Notifications never execute
alarm commands. See the [notification guide and blueprint](docs/automation-notifications.md)
for the event vocabulary, dependencies, validated examples and delivery limits.

The primary automated validation target is HA Core 2026.11.2, matching the
separately observed household runtime. See the [quality evidence](docs/quality-status.md)
and [capability specifications](specs/CATALOG.md) for the tested scope and remaining limits.

## 🔧 Available Entities

Home Assistant assigns entity IDs from **friendly names** and **unique IDs** (see `custom_components/my_verisure/`). Typical patterns:

### Alarm Control Panel

- **Often**: `alarm_control_panel.my_verisure` (single panel per config entry; verify in **Developer tools → States**)
- **States**: `disarmed`, `armed_home`, `armed_away`, `armed_night`, transitional states during operations
- **Features**: ARM_HOME / ARM_NIGHT / ARM_AWAY

### Sensors

- **General Alarm Status**, **Active Alarms**, **Panel State** (good for automations), **Last Updated** — entity IDs depend on your install (see [Entities doc](docs/user-guide/entities.md))

### Binary Sensors

- **Internal Day / Night / Total**, **External** — zone booleans (`binary_sensor.*`)

### Cameras & button

- Snapshot **camera** entities and **Refresh Camera Images** button when devices exist — see [Entities](docs/user-guide/entities.md)

## 📖 Entity usage

See **[docs/user-guide/entities.md](docs/user-guide/entities.md)** and **[docs/user-guide/automations.md](docs/user-guide/automations.md)**.

## 🚨 Available Services

### `my_verisure.arm_away`

Arms interior total. The optional supplementary-perimeter setting also arms exterior.

```yaml
action: my_verisure.arm_away
data:
  installation_id: "YOUR_INSTALLATION_ID"
```

### `my_verisure.arm_home`

Arms exterior/perimeter only.

```yaml
action: my_verisure.arm_home
data:
  installation_id: "YOUR_INSTALLATION_ID"
```

### `my_verisure.arm_night`

Arms interior partial night, optionally followed by exterior/perimeter.

```yaml
action: my_verisure.arm_night
data:
  installation_id: "YOUR_INSTALLATION_ID"
```

### `my_verisure.disarm`

Disarms the alarm.

```yaml
action: my_verisure.disarm
data:
  installation_id: "YOUR_INSTALLATION_ID"
```

Additional services: `my_verisure.get_status`, `my_verisure.refresh_camera_images` — see **[docs/user-guide/services.md](docs/user-guide/services.md)**.

## 🛠️ Development

### Pinned offline setup

```bash
git clone https://github.com/efraespada/my_verisure.git
cd my_verisure
python3.14 -m venv .ha-2026.11-venv
make install
make test-ha-2026-11
```

`Makefile`, `./dev` and the HA validation script use
`.ha-2026.11-venv/bin/python` by default. To reuse another environment, export
`HA_PYTHON=/path/to/validation-env/bin/python` before the commands.
The suite uses synthetic data and sends no provider requests.

Start with [QUICKSTART.md](QUICKSTART.md). An optional local HA UI is described
in [local development](docs/developer-guide/local-development.md), including
pinned Docker and Dev Container configurations. Those container paths have
static configuration checks; the current audit did not start them.

### Testing System

The project includes a reproducible testing system:

#### 🧪 **Test Suites**

- CLI tests covering the command-line interface
- Core tests covering application and repository behavior
- Home Assistant lifecycle and platform tests

#### 📊 **Coverage Reports**

- Contextual integration, CLI and tooling line/branch coverage is generated by
  `make coverage` and is not committed. Package regression floors and the
  stricter notification-module gate are described in [quality status](docs/quality-status.md).

The [repository audit](docs/technical/2026-11-23-project-quality-audit.md) records
corrected defects, actual coverage gaps and operational limits. Dependency direction
is documented in [ADR 0001](docs/adr/0001-core-and-adapter-dependencies.md).

#### 🛠️ **Available Commands**

**Using the repository Makefile:**

```bash
make test-ha-2026-11  # Complete suite against HA Core 2026.11.2
make coverage        # Coverage report
make lint-critical   # CI-critical lint checks
make type-check      # Complete mypy gate
make git-check       # Architecture, documentation, compilation and dependencies
make docs-check      # Local Markdown links and SDD catalog paths
make ci              # All local release gates
```

The direct commands below are useful for focused debugging only:

```bash
python -m pytest cli/tests -q
python -m pytest custom_components/my_verisure/core/tests -q
```

#### 📋 **Dependencies**

All development dependencies are automatically installed from `requirements-dev.txt`:

```text
Home Assistant Core 2026.11.2
Python >=3.14.2
pytest-homeassistant 2026.11.2
```

### Project Structure

```
my_verisure/
├── cli/                    # Command-line interface
│   ├── commands/          # CLI commands
│   ├── tests/            # CLI tests
│   └── utils/            # CLI utilities
├── custom_components/     # Home Assistant integration
│   └── my_verisure/      # Integration and embedded application core
├── requirements-dev.txt   # Development/test dependencies
├── Makefile               # Canonical development and verification commands
├── scripts/               # Reproducible validation helpers
└── README.md             # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the gates: `make ci`
5. Ensure all tests pass and coverage is maintained
6. Open a pull request targeting `develop`. Release promotion uses a separate
   `develop` → `master` pull request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/efraespada/my_verisure/issues) page
2. Create a new issue with detailed information
3. Include versions, reproduction steps and sanitized errors; remove credentials, tokens, device identifiers and household details from attachments

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

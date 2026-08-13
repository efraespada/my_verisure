# My Verisure

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40efraespada-blue.svg)](https://github.com/efraespada)

Custom integration for Home Assistant that connects to the Verisure / Securitas Direct GraphQL API. Control alarm modes, read detailed zone status, refresh camera snapshots, and automate via services.

## 📚 Documentation

**Full documentation** (user guide, developer guide, architecture, API reference, examples, roadmap): **[docs/index.md](docs/index.md)** · [Documentation overview](docs/README.md)

Quick links: [Installation](docs/user-guide/installation.md) · [Configuration](docs/user-guide/configuration.md) · [Entities](docs/user-guide/entities.md) · [Services](docs/user-guide/services.md) · [Troubleshooting](docs/user-guide/troubleshooting.md)

## 🚀 Features

- ✅ **Complete authentication** with 2FA (OTP via SMS)
- ✅ **Automatic session management**
- ✅ **Multiple installations** supported
- ✅ **Alarm services** (arm/disarm, status)
- ✅ **Modern GraphQL API** (doesn't use obsolete `vsure` library)

## 📋 Requirements

- Home Assistant 2026.8.1 (Core; Python >=3.14.2)
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
2. Copy the `my_verisure` folder to `<config_dir>/custom_components/`
3. Restart Home Assistant
4. Configure the integration from the interface

## ⚙️ Configuration

1. Go to **Settings** > **Devices & Services** > **Integrations**
2. Search for "My Verisure" and click "Configure"
3. Enter your **DNI/NIE** (without hyphens)
4. Enter your **password**
5. Select the **phone** to receive the OTP code
6. Enter the **OTP code** you receive via SMS
7. Done! The integration will configure automatically

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

Arms the alarm in away mode.

```yaml
service: my_verisure.arm_away
data:
  installation_id: "6220569"
```

### `my_verisure.arm_home`

Arms the alarm in home mode.

```yaml
service: my_verisure.arm_home
data:
  installation_id: "6220569"
```

### `my_verisure.arm_night`

Arms the alarm in night mode.

```yaml
service: my_verisure.arm_night
data:
  installation_id: "6220569"
```

### `my_verisure.disarm`

Disarms the alarm.

```yaml
service: my_verisure.disarm
data:
  installation_id: "6220569"
```

Additional services: `my_verisure.get_status`, `my_verisure.refresh_camera_images` — see **[docs/user-guide/services.md](docs/user-guide/services.md)**.

## 🛠️ Development

### Quick Start

New to the project? Start here: **[QUICKSTART.md](QUICKSTART.md)** (5-minute setup)

### Local Home Assistant Setup

#### Option A: Docker Standalone (Recommended for OrbStack)

If you're using OrbStack, use this simple Docker setup:

```bash
# Start Home Assistant
./dev docker-start

# Access at http://localhost:8123

# View logs
./dev docker-logs

# Stop
./dev docker-stop
```

**See complete guide:** [OrbStack Setup](ORBSTACK_SETUP.md)

#### Option B: DevContainer (For Docker Desktop + Cursor/VS Code)

For Docker Desktop users who want integrated debugging:

```bash
# Using the dev helper script
./dev devcontainer  # Opens in Cursor/VS Code DevContainer
./dev start         # Start Home Assistant
./dev logs          # View logs

# Or manually
cursor .            # Open in Cursor (or: code .)
# Reopen in Container (Cursor will prompt you)
container start     # Start Home Assistant
# Access at http://localhost:7123
```

**Cursor users:** Works identically to VS Code! All DevContainer features, debugging, and extensions are fully compatible.

**See complete guides:**

- [Local Development Setup](docs/developer-guide/local-development.md)
- [OrbStack Setup](ORBSTACK_SETUP.md) ← Use this if you have OrbStack

### Quick Setup (CLI/Core Development)

To set up the development environment for CLI and core library development:

```bash
# Clone the repository
git clone <repository-url>
cd my_verisure

# Create and activate virtual environment
python3.14 -m venv .ha-2026.8-venv
source .ha-2026.8-venv/bin/activate  # Windows: use an equivalent Python 3.14 environment

# Install the pinned validation dependencies
HA_PYTHON=/tmp/ha-2026.8.1-venv/bin/python make install
```

### Testing System

The project includes a reproducible testing system:

#### 🧪 **Test Suites**

- CLI tests covering the command-line interface
- Core tests covering application and repository behavior
- Home Assistant lifecycle and platform tests

#### 📊 **Coverage Reports**

- Contextual coverage is generated by `make coverage` and is not committed.

#### 🛠️ **Available Commands**

**Using the repository Makefile:**

```bash
make test-ha-2026-8  # Complete suite against HA Core 2026.8.1
make coverage        # Coverage report
make lint-critical   # CI-critical lint checks
make type-check      # Complete mypy gate
make git-check       # Architecture, compilation and dependencies
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
Home Assistant Core 2026.8.1
Python >=3.14.2
pytest-homeassistant-custom-component 0.13.355
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
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/efrain.espada/my_verisure/issues) page
2. Create a new issue with detailed information
3. Include logs and configuration details

## 📈 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

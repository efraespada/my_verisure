# My Verisure

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40efrain.espada-blue.svg)](https://github.com/efrain.espada)

Custom integration for Home Assistant that connects to the new Verisure/Securitas Direct GraphQL API. This integration provides full control over your Verisure security system including alarm control, sensors, cameras, and smart locks.

## 🚀 Features

- ✅ **Complete authentication** with 2FA (OTP via SMS)
- ✅ **Automatic session management**
- ✅ **Multiple installations** supported
- ✅ **Alarm services** (arm/disarm, status)
- ✅ **Modern GraphQL API** (doesn't use obsolete `vsure` library)

## 📋 Requirements

- Home Assistant 2024.1.0 or higher
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

### Alarm Control Panel
- **Entity ID**: `alarm_control_panel.my_verisure_alarm_{installation_id}`
- **States**: `disarmed`, `armed_home`, `armed_away`, `armed_night`, `arming`, `disarming`
- **Features**: Full alarm control with visual interface

### Sensors
- **Alarm Status**: `sensor.my_verisure_alarm_status_{installation_id}` - Detailed alarm status
- **Active Alarms**: `sensor.my_verisure_active_alarms_{installation_id}` - List of active alarms
- **Panel State**: `sensor.my_verisure_panel_state_{installation_id}` - **Perfect for automations**
- **Last Updated**: `sensor.my_verisure_last_updated_{installation_id}` - Timestamp of last update

### Binary Sensors
- **Internal Day**: `binary_sensor.my_verisure_alarm_internal_day_{installation_id}`
- **Internal Night**: `binary_sensor.my_verisure_alarm_internal_night_{installation_id}`
- **Internal Total**: `binary_sensor.my_verisure_alarm_internal_total_{installation_id}`
- **External**: `binary_sensor.my_verisure_alarm_external_{installation_id}`

## 📖 Entity Usage Guide

For detailed information on how to use these entities in automations, dashboards, and scripts, see the [Entities Guide](ENTITIES_GUIDE.md).

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
  code: "1234"
```

## 🛠️ Development

### Quick Setup

To set up the development environment:

```bash
# Clone the repository
git clone <repository-url>
cd my_verisure

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the setup script (installs all dependencies automatically)
python setup_development.py
```

### Testing System

The project includes a comprehensive testing system:

#### 🧪 **Test Suites**
- **CLI Tests**: 92 tests covering command-line interface
- **Core Tests**: 137 tests covering business logic
- **Integration Tests**: Complete integration testing
- **Total**: 229 tests with 100% pass rate

#### 📊 **Coverage Reports**
- **CLI Coverage**: 57% with detailed reports
- **Core Coverage**: 34% with detailed reports
- **HTML Reports**: Available in `htmlcov/` directory

#### 🛠️ **Available Commands**

```bash
# Run all tests with coverage
python run_all_tests.py

# Run specific test suites
python run_cli_tests.py                    # CLI tests only
python run_coverage.py cli         # CLI coverage
python run_coverage.py core        # Core coverage
python run_coverage.py             # Full coverage

# Individual tools
python -m pytest cli/tests/ -v             # CLI tests
python -m pytest core/tests/ -v            # Core tests
python -m coverage run -m pytest cli/tests # Manual coverage
python -m coverage report                  # Coverage report
python -m coverage html                    # HTML report

# Code quality tools
flake8 cli/ core/                          # Linting
mypy cli/ core/                            # Type checking
black cli/ core/                           # Code formatting
```

#### 📋 **Dependencies**

All development dependencies are automatically installed from `requirements.txt`:

```txt
# Core dependencies
aiohttp>=3.8.0
gql[requests]>=3.4.0
voluptuous>=0.13.0

# Development tools
pytest>=8.4.0
pytest-asyncio>=0.21.0
pytest-cov>=6.2.0
pytest-mock>=3.14.0
pytest-timeout>=2.4.0
coverage>=7.10.0
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
```

#### 🔍 **Verification Scripts**

- `setup_development.py`: Complete environment setup
- `check_coverage.py`: Coverage verification and diagnostics
- `run_all_tests.py`: Complete test suite execution

### Project Structure

```
my_verisure/
├── cli/                    # Command-line interface
│   ├── commands/          # CLI commands
│   ├── tests/            # CLI tests
│   └── utils/            # CLI utilities
├── core/                  # Core business logic
│   ├── api/              # API clients and models
│   ├── repositories/     # Data access layer
│   ├── use_cases/        # Business logic
│   └── tests/            # Core tests
├── custom_components/     # Home Assistant integration
│   └── my_verisure/      # Integration code
├── requirements.txt       # Dependencies
├── setup_development.py   # Development setup
├── run_all_tests.py      # Test runner
└── README.md             # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite: `python run_all_tests.py`
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
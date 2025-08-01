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
```

### `my_verisure.get_status`
Refreshes the alarm status.

```yaml
service: my_verisure.get_status
data:
  installation_id: "6220569"
```

## 🔍 Troubleshooting

### Authentication error
- Verify that your DNI/NIE and password are correct
- Make sure your account is not blocked
- Try the password recovery process if necessary

### OTP error
- Verify that the phone number is correct
- Make sure you have mobile coverage
- The OTP code expires in 5 minutes

### Connection error
- Verify your internet connection
- The Verisure API may be temporarily unavailable

## 📝 Logs

To debug issues, enable detailed logs in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.my_verisure: debug
```

## 🤝 Contributing

1. Fork this repository
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is under the MIT License. See the `LICENSE` file for more details.

## ⚠️ Disclaimer

This integration is not officially supported by Verisure/Securitas Direct. It is a community project developed for personal use.

## 🆘 Support

If you have problems:

1. Check the troubleshooting section
2. Search in [existing issues](https://github.com/tu-usuario/my_verisure/issues)
3. Create a new issue with:
   - Home Assistant version
   - Error logs
   - Steps to reproduce the problem

## 🗺️ Roadmap

- [ ] Camera support
- [ ] Lock support
- [ ] Push notifications
- [ ] Automatic scheduling
- [ ] Google Home/Alexa integration
- [ ] Custom dashboard

---

**Do you like this integration? Give the repository a ⭐!** 
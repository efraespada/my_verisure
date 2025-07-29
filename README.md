# My Verisure

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![maintainer](https://img.shields.io/badge/maintainer-%40efrain.espada-blue.svg)](https://github.com/efrain.espada)

Custom integration for Home Assistant that connects to the new Verisure/Securitas Direct GraphQL API. This integration provides full control over your Verisure security system including alarm control, sensors, cameras, and smart locks.

## 🚀 Features

- ✅ **Complete authentication** with 2FA (OTP via SMS)
- ✅ **Automatic session management**
- ✅ **Multiple installations** supported
- ✅ **Alarm services** (arm/disarm, status)
- ✅ **Cameras** and **locks** (coming soon)
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
- **Alarm status**: Armed, Disarmed, Perimeter, etc.
- **Control**: Arm/Disarm, Arm day, Arm night, Perimeter

### Binary Sensors
- **Zone status**: Motion detectors, doors, etc.
- **System status**: Failures, low battery, etc.

### Sensors
- **Installation information**: Panel, SIM, IBS
- **Service status**: Active/inactive services

### Cameras (coming soon)
- **Security cameras**: Image and video capture

### Locks (coming soon)
- **Smart locks**: Door control

## 🚨 Available Services

### `my_verisure.arm_alarm`
Arms the alarm with the specified mode.

```yaml
service: my_verisure.arm_alarm
data:
  installation_id: "6220569"
  mode: "day"  # day, night, perimeter, total
```

### `my_verisure.disarm_alarm`
Disarms the alarm.

```yaml
service: my_verisure.disarm_alarm
data:
  installation_id: "6220569"
```

### `my_verisure.get_alarm_status`
Gets the current alarm status.

```yaml
service: my_verisure.get_alarm_status
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
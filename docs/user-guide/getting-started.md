# Getting started

## What you get

- **Alarm control** via the native alarm panel entity and domain services  
- **Rich status** via text sensors and binary sensors for internal day/night/total and perimeter  
- **Cameras** backed by refreshed images on disk (see [Entities](entities.md))  
- **Cloud polling** — the integration contacts Securitas Direct’s GraphQL API; there is no local LAN API  

## Prerequisites

- **Home Assistant:** 2026.8.1 (Core; Python >=3.14.2)
- **Verisure / Securitas Direct (Spain)** account credentials used in the official app  
- **Network** — outbound HTTPS to `customers.securitasdirect.es`  

## Five-minute setup

1. Install the integration ([Installation](installation.md)) via HACS or by copying `custom_components/my_verisure`.  
2. Restart Home Assistant.  
3. **Settings → Devices & services → Add integration → My Verisure.**  
4. Enter **user** (DNI/NIE as used in the app) and **password**.  
5. If prompted for **OTP**, pick a phone number and enter the SMS code ([Configuration](configuration.md)).  
6. Select **installation** (site) to bind this config entry.  
7. Confirm entities appear under the new device ([Entities](entities.md)).  

## Next steps

- Tune **polling interval** and **auto arm perimeter** in integration **Options** ([Configuration](configuration.md)).  
- Use **Panel State** or **Active Alarms** sensors in automations ([Automations](automations.md)).  

## Assumptions

- Documentation describes behavior **as implemented in this repository**. Regional or account-specific API differences may apply; if something differs in production, treat it as an API or account variance and capture logs ([Troubleshooting](troubleshooting.md)).

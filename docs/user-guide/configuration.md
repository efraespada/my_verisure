# Configuration

My Verisure uses a **Config Flow** (`config_flow.py`). There is no documented YAML configuration for initial setup.

## Config entry data (stored)

Populated during the flow (see [`config_flow.py`](../../custom_components/my_verisure/config_flow.py)):

| Key | Constant | Description |
|-----|----------|-------------|
| User | `CONF_USER` | Account identifier (e.g. DNI/NIE as used in the mobile app) |
| Password | `CONF_PASSWORD` | Account password |
| Installation ID | `CONF_INSTALLATION_ID` | Selected Securitas installation (`numinst`) |
| Scan interval | `CONF_SCAN_INTERVAL` | Initial polling interval in **minutes** (default from `DEFAULT_SCAN_INTERVAL` = **10** in [`core/const.py`](../../custom_components/my_verisure/core/const.py)) |

Phone / OTP steps use `CONF_PHONE_ID` and `CONF_OTP_CODE` during the flow only.

## Authentication flow (summary)

1. **User step** — credentials submitted; `AuthUseCase.login` runs.  
2. **OTP path** — if `MyVerisureOTPError` is raised, the flow may show **phone selection** then **OTP verification** (`verify_otp`).  
3. **Installation step** — installations are listed; user picks one. Entry is created with title `My Verisure - {alias or id}`.  

If login succeeds without OTP, installation selection follows directly.

## Options flow

**Settings → My Verisure → Configure** opens `MyVerisureOptionsFlowHandler`:

| Option | Constant | Purpose |
|--------|----------|---------|
| Scan interval (minutes) | `CONF_SCAN_INTERVAL` | Coordinator `update_interval` ([Coordinator](../developer-guide/coordinator.md)) |
| Immediate photo updates | `CONF_PUSH_ENABLED` | Default false. FCM completion keeps status polling as fallback and may request device verification by SMS. |
| Auto arm perimeter with internal | `CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL` | Default false for new entries; adds exterior after a successful interior Away or Night command when enabled |

Disabling immediate updates stops the receiver and keeps the verified native device
profile and ordinary polling. Re-enabling reuses its private receiver credentials.
No inbound port or Firebase server credential is needed.

Options override entry `data` for scan interval (see `update_listener` in [`integration.py`](../../custom_components/my_verisure/integration.py)).

## Session persistence

- Session material is entry scoped under `.storage/my_verisure_<entry_id>/data/`; separate entries do not share sessions, device identity or snapshots.
- Authentication uses the stored native refresh token when possible. Password login and a device-bound SMS challenge are used when required; the selected phone identifier may validly be zero.
- Successful SMS verification is followed by native login. Authentication is published only after the token pair is persisted; failed persistence restores the previous session.
- Alarm commands authenticate first and refresh installation permissions when their session binding changes or their capability JWT expires. Failed permission refresh prevents the command.
- Reauthentication keeps the existing entry and entity identities.

For deeper behavior see [Session persistence](../technical/session-persistence.md).

## Current alarm mapping

| HA control | Verisure command |
|---|---|
| Home / En casa | Exterior only (`PERI1`) in the current implementation |
| Night / Noche | Interior partial night (`ARMNIGHT1`), optionally followed by exterior |
| Away / Ausente | Interior total (`ARM1`), optionally followed by exterior |
| Disarm / Desarmar | Disconnect (`DARM1`) |

The supplementary exterior option applies to both interior modes. The owner
confirmed that Home remains exterior-only. See the
[alarm contract](../../specs/alarm-modes-and-confirmation.md).

## Service blocked / rate limiting

`MyVerisureServiceBlockedError` triggers a **persistent notification** and failed update (`UpdateFailed`). See [Troubleshooting](troubleshooting.md).

# Entities

Entities are created **per config entry** (one installation per entry). Platform setup is in [`integration.py`](../../custom_components/my_verisure/integration.py).

Friendly names come from `ENTITY_NAMES` in [`core/const.py`](../../custom_components/my_verisure/core/const.py).

## Naming and IDs

| Platform | Naming | `unique_id` pattern (typical) |
|----------|--------|--------------------------------|
| Alarm control panel | `ENTITY_NAMES["alarm_control_panel"]` → **"My Verisure"** | `my_verisure-{entry_id}` |
| Sensors | Per-sensor friendly name | `{entry_id}_{sensor_id}` e.g. `{entry}_alarm_status` |
| Binary sensors | Per-sensor friendly name | `{entry_id}_alarm_{sensor_id}` |
| Cameras | `Verisure {device name}` | `{entry_id}_camera_{opaque_device_digest}` |
| Button | `Refresh Camera Images` | `{entry_id}_refresh_camera_images` |
| Reported event | Verisure notices | `{entry_id}_notifications` |
| Confirmed event | Verified results | `{entry_id}_confirmed_results` |
| Push diagnostics | Connection, binding, receipt/verification times, cooldown | `{entry_id}_push_{diagnostic}` |

Unique IDs are scoped to the config entry. Camera identity uses a digest of the
entry, provider device type and code, so list reordering does not change it.
The registry migration preserves unambiguous existing entity IDs, areas and
customization. Reauthentication and updates retain the original entry; do not
remove/re-add it as a routine session refresh.

Entity IDs in the UI will look like `alarm_control_panel.my_verisure`, `sensor.<slug>`, etc., depending on HA’s slug rules.

## Alarm control panel

**Class:** `MyVerisureAlarmControlPanel` in [`alarm_control_panel.py`](../../custom_components/my_verisure/alarm_control_panel.py).

**Features:** ARM_AWAY, ARM_HOME, ARM_NIGHT (`AlarmControlPanelEntityFeature`).  
**Codes:** `code_arm_required` and `code_disarm_required` are **False** in code — disarm does not use an HA alarm code (Securitas validates on API side).

**State mapping (summary):** Primary HA state is derived from internal day/night/total and external flags with priority **Total → Night → Day → External → Disarmed**. Transition states **arming** / **disarming** may be shown for UX during operations.

See [alarm-control-panel.md](../api-reference/entities/alarm-control-panel.md) for attributes and behavior details.

## Sensors

All in [`sensor.py`](../../custom_components/my_verisure/sensor.py):

| Purpose | `sensor_id` | Friendly name (const) |
|---------|---------------|------------------------|
| Aggregate text status | `alarm_status` | General Alarm Status |
| Human-readable active modes | `active_alarms` | Active Alarms |
| Automation-friendly panel state | `panel_state` | Panel State |
| Last coordinator refresh | `last_updated` | Last Updated |

**Alarm status** strings include values such as `Total Internal Active`, `Internal Day Active`, `Perimeter Active`, `Alarm Disarmed`, etc., based on internal/external booleans (English strings in code).

## Binary sensors

Device class **SAFETY**. Types: **internal_day**, **internal_night**, **internal_total**, **external** — each reflects the corresponding flag in coordinator alarm payload.

## Cameras

[`camera.py`](../../custom_components/my_verisure/camera.py): images are read from on-disk paths under the integration file manager (`cameras/{type}{code}/timestamp dirs`). No RTSP/stream — **still image** from the latest complete committed capture.
Optional FCM completion verifies the exact signal, camera and freshness before
commit; the existing 20-second status polling remains available. An older displayed
image does not prove a new request succeeded. See the [camera reference](../api-reference/entities/cameras.md).

## Buttons

**Refresh Camera Images** triggers the domain service `my_verisure.refresh_camera_images` for the installation ([Services](services.md)).

## Notification events and diagnostics

The two event entities expose 13 finite reported types and three confirmed types.
Restoring their last display does not replay automations. Their availability is
independent of the socket/API connection, so the first new event after reconnect
is retained. Account/personal messages without a verified installation remain in
sanitized diagnostics rather than the household event stream.

The connection binary sensor is enabled by default. Binding state, last received,
last accepted, last verified and cooldown sensors are diagnostic entities disabled
by default. Their attributes contain no raw messages or provider identifiers.
The diagnostic download adds bounded counters, a safe recent ring, category
coverage and last authoritative state-sync time. A quiet channel is not itself an error.
See [notification automations](../automation-notifications.md).

## Device registry

[`device.py`](../../custom_components/my_verisure/device.py) supplies device info (manufacturer Verisure, model Alarm System, etc.).

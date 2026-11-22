# Alarm control panel

**Implementation:** [`alarm_control_panel.py`](../../../custom_components/my_verisure/alarm_control_panel.py)  
**Friendly name:** `ENTITY_NAMES["alarm_control_panel"]` → **My Verisure**  
**Unique ID:** entry-scoped `"my_verisure-<entry_id>"`; migration preserves the
original entity ID so existing automation references remain valid.

## Supported features

`ARM_AWAY | ARM_HOME | ARM_NIGHT` (`AlarmControlPanelEntityFeature`).

## Codes

`code_format=None`; arm/disarm **without** HA alarm code UI — vendor validates remotely.

## States

Uses `AlarmControlPanelState` values:

- Derived primary state from nested booleans in API payload (`internal.day/night/total`, `external.status`).  
- Shows **arming** / **disarming** until the awaited HA service completes; clears
  the transition on success, failure or cancellation.
- Native confirmed D/E/Q/C codes update all protection flags directly. An
  unconfirmed mutation invalidates stale state instead of showing the prior
  disarmed value as current. Unsupported confirmation codes trigger a bounded
  fallback read; its failure does not turn an accepted command into a rejection.

Home currently means exterior; Night means partial night, optionally with exterior;
Away means interior total, optionally with exterior. The owner confirmed the
Home mapping. See the [mode contract](../../../specs/alarm-modes-and-confirmation.md).

## Attributes

Include parsed booleans and human-readable `active_alarms` list members (`Internal Total`, `Internal Day`, …) — exact keys mirror `_analyze_alarm_states` output.

## Related services

Standard HA services apply (`alarm_control_panel.alarm_arm_*`, `alarm_disarm`) in addition to integration-specific [`my_verisure.*`](../README.md#services) services.

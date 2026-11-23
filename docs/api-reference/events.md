# Events

My Verisure provides two Home Assistant **event entities** per loaded entry:
**Verisure notices** (reported provider messages) and **Verified results**
(independently checked outcomes). Their state is the last event timestamp, not
the current alarm state.

| Entity | `event_type` values |
|---|---|
| Notices | `photo_reported`, `alarm_operation_reported`, `security_incident_reported`, `arm_reminder`, `unprotected_home`, `smart_disarm_notice`, `device_maintenance_notice`, `device_tamper_reported`, `maintenance_appointment`, `support_reply`, `account_notice`, `generic_notice`, `unclassified_notice` |
| Results | `photo_ready`, `alarm_state_confirmed`, `incident_status_confirmed` |

Observation defaults to enabled. Push reception must also be enabled to receive
provider messages; selective state reads and external photo retrieval are
separate opt-in options. Local verified operations can publish results without
a received provider message. These options never issue alarm commands.

## Advanced bus

Enable **Settings → Devices & Services → My Verisure → Configure → Advanced
event bus** to mirror the same safe envelope on `my_verisure_event`.
The option defaults to disabled and requires notification observation.

The version-1 envelope includes `kind`, `stage`, `event_id`, `correlation_id`,
`category`, `scope`, timestamps, `freshness`, `delivery`, `verification`,
`subject_entity_id` and permitted facts. The bus additionally includes
`config_entry_id`; an event entity exposes HA's standard `event_type` attribute.
It contains no provider free text, credentials, original signal/account IDs,
URLs or images. Choose either the event entity or the bus for one automation:
they mirror the same `event_id`.

Use `freshness: fresh`, `delivery: live` and an appropriate verified result for
actions with effects. Restoration does not publish a new live event. A reported
notice alone does not prove the current alarm state; delivery of every category
has not been established. Preserve polling and make downstream actions
idempotent.

See the [complete contract, examples and blueprint](../automation-notifications.md)
and [notification specification](../../specs/notification-observability-and-automation.md).

# Automations

## When state changes

Prefer **`sensor.<panel_state>`** or **`sensor.<active_alarms>`** triggers when you need stable text for conditions. Binary sensors are ideal for **zone-specific** logic (perimeter vs internal total).

### Notify on perimeter active

```yaml
alias: Verisure perimeter on
trigger:
  - platform: state
    entity_id: binary_sensor.my_verisure_alarm_external
    to: "on"
action:
  - service: notify.persistent_notification
    data:
      title: Perimeter armed
      message: External perimeter is active
```

Replace entity IDs with yours from **Developer tools**.

### Refresh status before bedtime

```yaml
alias: Verisure refresh at 22:30
trigger:
  - platform: time
    at: "22:30:00"
action:
  - action: my_verisure.get_status
    data:
      installation_id: "YOUR_INSTALLATION_ID"
```

## Using services instead of the panel

Use **`my_verisure.arm_*` / `disarm`** when you want explicit service calls (e.g. from scripts or Amazon Alexa routines calling HA services).

```yaml
action:
  - action: my_verisure.arm_night
    data:
      installation_id: "YOUR_INSTALLATION_ID"
```

## Rate limiting

The integration is **cloud polled**. Avoid hammering `get_status` in tight loops; respect your configured **scan interval** ([Configuration](configuration.md)).

## More examples

- [examples/automations/](../examples/automations/)  
- [Multiple alarms](multiple-alarms.md)  

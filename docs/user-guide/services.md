# Services

Services are registered in [`services.py`](../../custom_components/my_verisure/services.py) and described for the UI in [`services.yaml`](../../custom_components/my_verisure/services.yaml).

**Domain:** `my_verisure`

Handlers locate loaded config entries for the domain and use each entry's
`runtime_data` coordinator, matching `config_entry.data["installation_id"]`.

## `my_verisure.arm_away`

**Data:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `installation_id` | Yes | string | Installation ID (`numinst`) |

Calls `coordinator.async_arm_away()` to arm interior total. May use **auto arm perimeter with internal** from options/data (`CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL`).

## `my_verisure.arm_home`

| Field | Required | Type |
|-------|----------|------|
| `installation_id` | Yes | string |

Calls `coordinator.async_arm_home()` to arm exterior/perimeter only.

## `my_verisure.arm_night`

| Field | Required | Type |
|-------|----------|------|
| `installation_id` | Yes | string |

Calls `coordinator.async_arm_night()` to arm interior partial night, with the same optional perimeter flag as arm_away.

## `my_verisure.disarm`

| Field | Required | Type |
|-------|----------|------|
| `installation_id` | Yes | string |

Disarm uses the authenticated Verisure API. The validated schema accepts
`installation_id`; no Home Assistant alarm code is required or accepted.

## `my_verisure.get_status`

Triggers `coordinator.async_request_refresh()` for the installation (forces an update cycle).

## `my_verisure.refresh_camera_images`

Runs the camera refresh use case. Supply optional `camera_entity_id` to refresh
only an existing camera owned by that entry; omit it to refresh all eligible
cameras. Concurrent refreshes are rejected. If enabled, FCM can complete the
pending photo after authoritative validation; otherwise the existing polling
schedule continues. Failure preserves the previous complete image and raises a
safe Home Assistant error. See [the service contract](../api-reference/services/refresh-camera-images.md).

## Example (YAML)

```yaml
action: my_verisure.arm_away
data:
  installation_id: "1234567"
```

```yaml
action: my_verisure.get_status
data:
  installation_id: "1234567"
```

## Related

- Per-service pages: [api-reference/services/](../api-reference/services/)

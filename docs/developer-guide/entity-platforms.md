# Entity platforms

Mapped in [`integration.py`](../../custom_components/my_verisure/integration.py):

```python
PLATFORMS = [
    alarm_control_panel,
    binary_sensor,
    sensor,
    camera,
    button,
]
```

Each `async_setup_entry` reads its coordinator from `config_entry.runtime_data`.
Stable entry-scoped unique IDs avoid collisions; unambiguous legacy registry rows
are migrated without replacing existing entity IDs.

## Patterns

- **Alarm / sensors / binary sensors**: manual `CoordinatorEntity`-style wiring — entities hold coordinator reference and read `coordinator.data`.  
- **Cameras**: `CoordinatorEntity` + `Camera`, latest complete committed filesystem capture; optional FCM completion with polling fallback.
- **Button**: triggers service `refresh_camera_images`.

When adding a new platform:

1. Add platform file + `async_setup_entry`.  
2. Register platform in `PLATFORMS`.  
3. Document entity in [api-reference](../api-reference/README.md).

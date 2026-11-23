# Service `my_verisure.arm_home`

**Schema:** requires `installation_id` (string).

Calls `coordinator.async_arm_home()`.

The current implementation sends exterior/perimeter `PERI1`. It does not activate
an interior partial mode. The owner confirmed this mapping; existing automation
behavior is preserved. See the [mode contract](../../../specs/alarm-modes-and-confirmation.md).

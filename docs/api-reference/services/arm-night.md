# Service `my_verisure.arm_night`

**Schema:** requires `installation_id` (string).

Calls `coordinator.async_arm_night()` with optional **`CONF_AUTO_ARM_PERIMETER_WITH_INTERNAL`** behavior.

The interior command is `ARMNIGHT1`. With the perimeter option enabled, wait for
its confirmation and then send exterior `PERI1` using the current panel state.
The option defaults to false for new entries and also applies to Away. Known
native completion states Q (night) and C (night plus exterior) publish directly
without an additional radio status check.

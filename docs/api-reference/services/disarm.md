# Service `my_verisure.disarm`

**Schema:** requires `installation_id` (string). `code` is not accepted.

Calls `coordinator.async_disarm()` using the entry's authenticated provider
session and current installation permissions. No HA panel PIN is required.
Failure is returned as a Home Assistant service error; it is not reported as a
successful disarm. This service changes physical alarm state.

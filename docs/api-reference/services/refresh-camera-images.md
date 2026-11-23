# Service `my_verisure.refresh_camera_images`

**Schema:** requires `installation_id`; accepts optional `camera_entity_id`.

Supply a camera entity belonging to that installation's config entry to request
only that camera. Omit it to refresh all eligible cameras, as before. A missing,
foreign or ambiguous camera selection fails before any photo request.

```yaml
action: my_verisure.refresh_camera_images
data:
  installation_id: "YOUR_INSTALLATION_ID"
  camera_entity_id: camera.your_verisure_camera
```

Calls `coordinator.async_refresh_camera_images()` with the selected camera's
internal identifier. The coordinator serializes refresh work: another request
while one is active is rejected rather than queued. The button remains busy
until the blocking action finishes; failed requests propagate an action error.
Its busy state is cleared on success, failure or cancellation.

The use case and repository forward the attempt/interval budget to the client.
The polling fallback remains 20 seconds. With immediate photo updates enabled,
an authenticated FCM hint can complete the same pending request after its exact
camera, signal and freshness are verified. It creates no additional photo mutation.
Provider failures retain the last complete image and return a safe Home Assistant
error. See the [push baseline](../../../specs/linux-push-photo-completion.md).
Do not run rapid repeated refreshes or schedule every camera at short intervals.
An existing displayed image is not proof that a new capture succeeded.

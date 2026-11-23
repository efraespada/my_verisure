# Cameras

[`camera.py`](../../../custom_components/my_verisure/camera.py)

## Behavior

- Entity derives snapshot bytes by scanning latest timestamp-named subdirectory under integration-managed camera folders.  
- **No streaming** features (`supported_features = 0`).  
- Cameras belong to the entry-owned alarm device. Their opaque unique ID hashes
  the entry ID, provider device type and code; list reordering does not change
  identity or expose the provider code in the unique ID.
- Migration preserves existing entity IDs and custom names only when a legacy
  camera can be matched unambiguously. Nullable metadata remains unknown; only
  an explicit inactive flag excludes a present camera from image requests.
- HA's camera base is initialized to create the access-token state required by
  its image endpoints. Camera setup does not duplicate coordinator refreshes.
- Default display names use the camera alias supplied by Verisure. Existing
  entity IDs and user-assigned names are preserved.

## Operational notes

If directories missing or parse fails, entity logs warnings and returns empty snapshot — run refresh flows ([refresh_camera_images](../../api-reference/services/refresh-camera-images.md)).

Snapshots are private, integration-managed static images. Seeing an existing image
does not establish that a new provider capture succeeded. A native fresh-photo
request and retrieval were captured, and a selected-camera HA refresh produced
three real images in 24.88 seconds. Broader camera coverage and image-age
presentation remain unverified. Use the optional camera selection on
the refresh action to avoid requesting every camera during a targeted check. See the
[data contract](../../../specs/installation-cameras-and-entity-identity.md).

## Immediate photo updates

Enable immediate photo updates in integration options to receive photo completion
through FCM. The receiver wakes only a pending request. The exact signal, selected
camera and timestamp are verified before committing all images. If no usable
event arrives, the original status polling continues at 20-second intervals.
Disabling the option retains the verified native device profile and polling.

A rejected request retains the last complete capture. Home Assistant reports a
safe error; wait before retrying. See the [push contract](../../../specs/linux-push-photo-completion.md)
and [actual HA receipt](../../validation/2026-11-23-ha-push.json).

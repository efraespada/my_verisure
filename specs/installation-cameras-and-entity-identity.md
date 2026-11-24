# Installation data, camera snapshots and stable HA identity

- Status: As-built baseline
- Date: 2026-11-22
- Catalog capability ID: installation-and-camera-data
- Last verified: 2026-11-23
- Owners: My Verisure maintainers
- Scope: installation/service/device projection, camera lifecycle and registry compatibility
- Required review gates: behavior, architecture, testing, documentation, security/operations
- Open decisions blocking readiness: broader camera coverage and freshness presentation remain unverified; production push has a separate verified baseline

## 1. Executive summary

An installation exposes its actual service/device data and stable HA entities.
Nullable provider metadata must remain unknown rather than aborting setup or
granting access. Camera identity must follow a device, not its position in a list.

## 2. Problem, current behavior and evidence

Observed native responses contained 54 services and nullable device `subtype`,
`remoteUse` and `isActive`. Omitting the configured Spanish language context
returned an empty services language. The integration now supplies that context
and keeps explicitly nullable metadata unknown through DTO/domain mappings.

Live HA setup exposed an uninitialized Camera base (`access_tokens` missing),
duplicate device/alarm registrations and camera index/code collisions after an
upstream identity change. Lifecycle initialization and an entry-scoped migration
restored one original device and 20 entities in the validated installation,
including the original alarm entity and its linked automations.

Intentional contract: preserve valid provider facts, public redaction and user
entity associations. A native fresh-photo request/retrieval has now been captured. The follow-up
forwards polling budgets, supports an entry-owned camera selection, rejects
overlap, propagates failures and uses provider aliases for default display names.
Selected-camera live HA captures and optional production push are verified;
broader camera coverage remains an acceptance requirement. Historic
motivation for list-index identity is unknown.

The future [complete physical-device registry](physical-device-inventory.md) is a
separate Draft. This baseline does not claim that every listed sensor already has
a dedicated HA device; current cameras share the installation hub.

## 3. Actors, surfaces and terminology

| Actor/surface | Responsibility |
|---|---|
| Verisure installation | authority for services, devices and capabilities |
| Entry coordinator | current in-memory installation/alarm snapshot |
| HA registry | persistent entity IDs, device area and customization |
| Camera entity | serve the most recent committed local snapshot |
| Owner | request fresh images and inspect freshness |

Discovery, provider activation, remote accessibility and the existence of a local
image are separate facts. `None` is not equivalent to an explicit false value.

## 4. Goals, non-goals and fixed invariants

- DATA-1: required identity fields MUST be validated; documented nullable fields MUST preserve null.
- DATA-2: remote accessibility MUST require explicit positive flags rather than unknown metadata.
- DATA-3: snapshot reads MUST ignore incomplete staging directories and invalid commit markers.
- DATA-4: camera identity MUST remain stable across provider reordering and distinct across entries/devices.
- DATA-5: registry migration MUST preserve unambiguous existing IDs/customization and avoid claiming another entry's device.
- DATA-6: ordinary entity attributes and persisted public snapshots MUST omit credentials, provider identifiers and private image paths.

Live streaming, smart-lock operation, device provisioning and reproducing the
official app's marketing/billing surfaces are outside the current integration's
implemented platforms. Their absence is not evidence of equivalent implementation.

## 5. Current versus intended journey

```mermaid
flowchart LR
    A[Authenticated entry] --> B[Services and capabilities]
    B --> C[Devices and installation details]
    C --> D[Validated domain snapshot]
    D --> E[Preserve registry identity]
    E --> F[HA sensors and cameras]
    F --> G[Explicit image refresh]
```

Text equivalent: authenticated installation → validated services/devices →
entry-owned snapshot → stable registry association → visible entities → explicit
image refresh. This baseline documents actual behavior. Native and HA fresh-photo
samples are verified; exhaustive camera parity remains an evidence requirement.

## 6. Functional behavior and state model

Services use the stable integration-owned UUID. Device reads include `remoteUse`.
Known camera types are YP and YR. Camera entities are discovered by type; image
use cases exclude cameras explicitly marked inactive. Unknown activation remains
unknown and does not grant remote accessibility.

| Image state | Meaning | Read behavior |
|---|---|---|
| No directory/image | no local bytes available | return no snapshot |
| Staging/uncommitted | incomplete write | ignore |
| Committed timestamp directory | complete local write | latest valid image/thumbnail |
| Provider refresh pending | awaiting provider result | bounded request/poll workflow |
| Refresh failure | previous image may remain | do not represent old bytes as a successful fresh capture |

The placeholder use case receives camera identifiers from the existing periodic
snapshot, with no additional provider reads. `LocalCameraPlaceholderStore` owns
Pillow/filesystem work behind `CameraPlaceholderStore`, preserves committed
images and drains its writer before cancellation returns. Placeholder failures
do not invalidate a valid alarm snapshot. Explicit CLI/config-flow discovery
remains available when no snapshot is supplied.

The current dummy-image use case can create placeholders. These are not real
provider photos; their UI/freshness distinction needs further review. The HA camera
class initializes its base lifecycle and serves static JPEGs without streaming.

## 7. User-facing configuration

The selected installation and entry-owned data directory determine device scope.
`scan_interval` is an exact integer from 1 to 1440 minutes, default 10;
invalid stored values recover to 10 minutes. Its standard integer form schema
serializes for HA; the application policy separately rejects boolean input; it does not request a new
photo on every image read. Image refresh is explicit through the button/service.
The refresh action accepts optional `camera_entity_id`; a foreign or unknown
selection fails before a provider mutation. Omitting it preserves all-camera
refresh. No supported setting turns unknown remote-access flags into positive permission.

Meaningful alternative: view the last stored snapshot without requesting new
provider images. The effective polling interval remains 20 seconds. Attempt and interval budgets
now reach the actual transport; a synthetic cross-boundary regression verifies
one mutation plus the configured maximum number of status reads.

## 8. Clean Architecture design

| Boundary | Owner |
|---|---|
| Provider schemas and transport | installation/camera clients and DTOs |
| Projection/domain | installation/device mappers and domain models |
| Device selection | pure `camera_devices.py` policy |
| Image workflow/storage | camera use cases, repository port, atomic image storage |
| HA presentation | camera/sensor/binary-sensor/button platforms |
| HA identity migration | `device.py`, `entity_registry_migration.py` |

`scripts/architecture_guard.py` checks dependency direction. HA registry APIs stay
in adapters; provider DTOs do not determine public entity attributes. Snapshot
persistence stores the sanitized alarm/service projection, not complete household
provider payloads. Installation details remain in memory.

## 9. UI/UX and content contract

| Condition | Meaning/action |
|---|---|
| Setup pending | installation loading; wait |
| Missing nullable metadata | entity remains discoverable; affected attributes are unknown |
| No image | no snapshot available; explicit refresh may be requested |
| Refresh pending | button indicates the in-progress request |
| Old image after failure | previous bytes retained; freshness must not imply success |
| Registry upgrade complete | original IDs/area/automation associations remain |

HA standard camera controls supply mobile/keyboard presentation. Default labels
use provider aliases while preserving custom names and entity IDs. The button
waits for action completion and resets after success, failure or cancellation;
overlapping requests are rejected without replay. Placeholder/failure freshness
still needs a dedicated manual UX review. A placeholder
or an idle camera entity is not proof of a live provider photo.

## 10. Failure, recovery and cleanup

Missing required data fails the affected projection; optional null values do not.
Failed writes must not expose partial image files. Preserve previous committed
images on failed refresh. Do not guess camera association from an old list index
or duplicate alias. Remove only identified empty integration-created duplicates;
retain ambiguous/customized entries for explicit review.

## 11. Security, permissions and privacy

Provider data and photos are private. Keep them outside public web directories,
diagnostic attributes and Git. Device/installation IDs do not appear in generic
public names or attributes. Opaque camera keys are entry-scoped. A migration
does not take ownership of another account/config entry's device.

## 12. Observability and operations

Record entity/service counts, nullable-field types, lifecycle errors and request
stages without raw payloads. Camera polling/retrieval timings remain a separate
measurement from alarm command completion. A captured native request completed
with a photo notice after about 21 seconds and then retrieved three images.
Its initial status response reported processing, not photo completion. Native
push transport and the installed optional Linux receiver are documented in
[`push-reception-investigation.md`](../docs/technical/push-reception-investigation.md).
Its isolated Linux receiver now has real delivery/decryption evidence; the
[separate baseline](linux-push-photo-completion.md) records installed production acceptance.
An official-app capture can identify
request order without authorizing repeated requests against every household camera.

## 13. Compatibility, migration, rollout and rollback

Legacy installation-keyed device IDs migrate to the entry-owned identity while
keeping the original device ID/area. The old global alarm entity migrates to the
entry-scoped unique ID while preserving its entity ID when the duplicate is empty.
Cameras use an opaque key derived from entry/type/code. Existing camera names in
generated entity IDs provide migration evidence; duplicate aliases are not guessed.
Keep a private HA registry rollback before migration.

## 14. Testing strategy and numeric budget

Maintenance minimum: 8 nullable/schema cases, 6 selection/permission cases,
6 storage/atomicity cases, 6 identity/migration cases, 4 lifecycle cases and
4 privacy/isolation cases: 34 distinct cases. Count overlap once.

Use projected GraphQL fixtures that return only selected fields, real HA registry
fixtures, reordered/duplicate camera lists, temporary storage and synthetic image
bytes. The repository now enforces separate line/branch floors for the
integration, CLI and tools; see [current measurements](../docs/quality-status.md).
Regressions cover invalid/empty/non-image/truncated encoded content, duplicate
photo identifiers and invalidation of a previous completion marker before
rewriting. Only a verified image commit can publish `photo_ready`. Static JPEG/PNG
containers are bounded before Pillow decoding; EXIF, profiles and unnecessary
metadata are removed without changing image pixels. Animated PNG and unsupported
containers fail closed. Image limits are 8 MiB decoded and 16 million pixels. Live photo evidence and a fresh-image UX review remain separate
from passing tests or successful entity creation.

## 15. Documentation and discoverability

| Path | Change |
|---|---|
| `docs/api-reference/entities/cameras.md` | update identity, lifecycle and image freshness |
| `docs/api-reference/services/refresh-camera-images.md` | reference explicit refresh and provider limits |
| `docs/user-guide/entities.md` | reference actual nullable data and stable identity |
| `specs/catalog.json` | register inspected data/media implementation evidence |

## 16. Acceptance scenarios

1. DATA-1: a native device with explicit null metadata loads; a missing required identity fails.
2. DATA-2: unknown active/remote flags do not grant remote accessibility.
3. DATA-3: partial staging or an invalid `.complete` marker is never served as a completed snapshot.
4. DATA-4: reversing the device list preserves each camera's opaque identity.
5. DATA-5: upgrading retains the original device area, alarm entity ID and unambiguous camera IDs; foreign ownership and duplicate aliases are not guessed.
6. DATA-6: diagnostics and public attributes exclude device codes, credentials and private paths.

## 17. Requirements traceability

| Requirement | Owner | Test/evidence |
|---|---|---|
| DATA-1/2 | DTO/domain/selection | `test_current_native_installation.py`, `test_camera_devices.py` |
| DATA-3 | storage/camera adapter | `test_camera_image_storage.py`, `test_ha_platforms.py` |
| Refresh budget/selection/failure | coordinator, use case, repository, action | `test_camera_refresh_boundaries.py`, `test_services_contracts.py`, `test_coordinator_update_boundaries.py`, `test_ha_diagnostics_button.py` |
| DATA-4/5 | identity/registry adapter | `test_entity_registry_migration.py`, reordering test in `test_ha_platforms.py`, live original-device count |
| DATA-6 | snapshot/redaction | `test_public_entity_redaction.py`, `test_ha_diagnostics_button.py` |

Full paths and documentation references are retained in the catalog.

## 18. Implementation or maintenance sequence

For future changes, establish the native request/response contract first, add a
synthetic regression, update policy/ports/adapters, exercise real HA lifecycle and
registry migration, verify storage/privacy, then perform bounded authorized live
image verification and publish only sanitized outcomes.

## 19. Definition of Done

- [x] Provider nullability, lifecycle and identity defects have source/test evidence.
- [x] Live registry migration preserves the original device and 20 installation-specific entities.
- [x] Native photo-request/retrieval and a selected-camera HA refresh have real fresh-image evidence.
- [x] Default camera aliases are visible in HA without replacing existing entity IDs.
- [x] Polling options reach the transport, overlapping refreshes are rejected and failures propagate.
- [ ] Placeholder/freshness UX and broader camera-family behavior are reviewed.
- [ ] Ambiguous duplicate-alias migration remains fail-closed; any automatic resolution requires a separate decision.
- [ ] Future Copilot specification tooling validates the chosen catalog/schema integration.

## 20. References and decisions

Reference process: [Copilot specification standard](https://github.com/vypdev/copilot/blob/master/specs/README.md).
Protocol evidence: owner-authorized native app and HA setup, 2026-11-22.
Related baselines: [authentication](native-authentication-and-session-lifecycle.md)
and [alarm control](alarm-modes-and-confirmation.md).

Production push follow-up: the [2026-11-23 HA receipt](../docs/validation/2026-11-23-ha-push.json)
supersedes this document's earlier production-push gap. Broader camera-family
coverage and stale-image presentation remain separate limitations.

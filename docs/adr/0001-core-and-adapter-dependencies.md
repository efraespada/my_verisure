# 0001: Keep policies independent of provider, HA and storage adapters

Status: accepted, 2026-11-23.

## Context

The project has two callers, Home Assistant and the CLI, and entry-owned state.
The repository audit found that the placeholder use case also implemented Pillow
and filesystem work, while snapshot policy imported `FileManager`. A periodic
refresh consequently fetched installation details again just to prepare local
placeholders, adding three avoidable cloud requests per cycle. An alarm dispatcher
port also exposed the HA `config_entry.data` shape.

## Decision

Keep values and policy in `core/application` and workflows in `core/use_cases`.
These modules depend on semantic interfaces, never HA, HTTP clients, provider
DTOs, dependency injection or concrete managers. Domain models import only
standard-library modules and other domain models. `core` as a whole imports no
Home Assistant package.

`CameraPlaceholderStore.ensure_placeholders(identifiers)` hides filesystem layout,
Pillow, staging, commit and cancellation ownership. Its local adapter performs no
provider queries. A periodic refresh supplies identifiers from the installation
snapshot already read. Explicit CLI/config-flow discovery may still read devices
once when the caller has no snapshot.

`CoordinatorSnapshotPersistence.save(snapshot)` is the refresh effect's only
storage dependency. `persistable_snapshot` remains a pure projection; the
concrete `core/coordinator_snapshot_store.py` adapter owns JSON/stat operations.
The alarm dispatcher's installation contract is `installation_id: str`, so a
plain Python object can satisfy it without a HA entry.

Composition roots select adapters. HA runtime data remains entry-owned; shared
provider cooldown/installation operation locks are deliberate coordination,
not a global account/session locator. Existing useful repository interfaces are
retained; introducing an interface for every library call would add no domain
behavior.

## Consequences and verification

The [AST guard](../../scripts/architecture_guard.py) checks absolute and relative
imports across all core production Python files. Synthetic forbidden-import
tests prevent regressions, including imports written as `from ... import api`.
The guard does not prove behavioral correctness or inspect dynamically generated
import targets.

Temporary-directory tests prove image publication and persistence, including
repeated cancellation. A coordinator pipeline regression requires exactly one
detailed installation read per periodic refresh. Optional placeholder failures
are logged without invalidating an otherwise valid state snapshot. Existing
images and public entity identities are retained.

Connection reuse in HTTP adapters and the size of the HA coordinator remain
maintainability/performance opportunities; the audit did not establish them as
remaining functional defects. See [the audit report](../technical/2026-11-23-project-quality-audit.md)
for scope, measurements and outstanding evidence limits.

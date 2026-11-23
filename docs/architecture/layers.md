# Layers and dependency direction

| Layer | Location | Responsibility |
|---|---|---|
| HA adapter | `coordinator.py`, `services.py`, entity platforms, `notification_runtime.py` | HA lifecycle, service errors, state/context projection and entry composition |
| CLI adapter | `cli/` | Command routing, terminal input/output and explicit composition |
| Application | `core/application/`, `core/use_cases/` | Policies, workflows and input/output ports independent of HA/HTTP/storage implementations |
| Domain values | `core/api/models/domain/` | Immutable business values; the historical path does not make them transport DTOs |
| Infrastructure adapters | `core/api/`, `core/repositories/implementations/`, persistence managers | HTTP, transport DTOs/mappers, provider framing and storage |
| Composition | `core/dependency_injection/` | One explicit graph per application/entry boundary |

Domain values do not import DTOs or framework clients. Application policies depend
on ports and domain values; infrastructure implements those ports. Transport
conversion belongs in mappers/adapters, rather than moving DTO dependencies
inward. HA's coordinator is an outer adapter even though it orchestrates calls.

These are dependency rules rather than a claim of perfect purity everywhere.
Some legacy HA projections still consume normalized dictionaries, and package
names retain historical organization. `scripts/architecture_guard.py` checks
selected forbidden imports/accessors; tests cover entry isolation and behavior.
Review changes against the actual dependencies as well as the guard.
See [composition ownership](../developer-guide/dependency-injection.md) and
[current evidence](../quality-status.md).

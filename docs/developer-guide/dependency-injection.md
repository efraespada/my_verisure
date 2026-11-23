# Dependency injection

[`CompositionRoot`](../../custom_components/my_verisure/core/dependency_injection/composition_root.py)
owns one Injector graph. Its production builder creates an explicit `FileManager`
and `SessionManager` for the supplied root and passes them to
[`MyVerisureModule`](../../custom_components/my_verisure/core/dependency_injection/module.py).
Use cases receive application ports; adapters implement those ports.

## Ownership and entry points

- `build_my_verisure_composition_root(project_root=..., push_enabled=...)`
  builds one application graph.
- `root.get(AuthUseCase)` and the other interface types resolve dependencies at
  that composition boundary; business policies do not call a global resolver.
- A config flow owns its temporary authentication graph. A loaded HA entry owns
  its coordinator and graph through `config_entry.runtime_data`.
- Entry-scoped storage isolates sessions, native device identity and snapshots.
  Unloading one entry drains its work and stops its receiver without clearing
  another entry's graph.

There is no `providers.py`, `setup_dependencies()` or `clear_dependencies()`
public API in the current package. Do not recreate a process-wide injector.

## Verification

`make git-check` runs `scripts/architecture_guard.py`. Composition, module scope,
concurrent entries and real HA setup/unload have tests in the core and HA suites.
These guards cover selected dependency rules; they do not prove every Clean
Architecture principle automatically. See [layers](../architecture/layers.md)
and [the capability catalog](../../specs/CATALOG.md) for the current boundaries.

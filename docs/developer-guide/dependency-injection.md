# Dependency injection

[`dependency_injection/providers.py`](../../custom_components/my_verisure/core/dependency_injection/providers.py) wires **injector** (`injector` package) with `MyVerisureModule`.

## Entry points

- `setup_dependencies()` — build injector  
- `get_auth_use_case()`, `get_alarm_use_case()`, … — resolve singletons  
- `clear_dependencies()` — tear down (called from coordinator cleanup)

## Why DI here?

Use cases depend on repository interfaces; repositories depend on API clients — DI keeps GraphQL wiring testable (see unit tests under `custom_components/my_verisure/core/tests/unit/`).

## Home Assistant lifecycle

Coordinator calls `setup_dependencies()` in `__init__` and may `clear_dependencies()` on cleanup — ensure no stale injector across tests / reloads.

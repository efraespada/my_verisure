# Testing

## Suites

| Area | Location | Notes |
|------|----------|-------|
| CLI | [`cli/tests/`](../../cli/tests/) | Commands, helpers, session |
| Home Assistant | [`custom_components/my_verisure/tests/`](../../custom_components/my_verisure/tests/) | Real HA config-entry, platform, event and lifecycle harness |
| Embedded core | [`custom_components/my_verisure/core/tests/unit/`](../../custom_components/my_verisure/core/tests/unit/) | Repositories, use cases, DTOs, session manager |

Tests are **pytest**-based. Current counts, measured coverage and limitations are recorded in [quality status](../quality-status.md).

## Useful commands

The root `Makefile` is the canonical interface and uses the pinned
Home Assistant validation environment:

```bash
make test-ha-2026-11
make test-cli
make test-core
make type-check
make lint-critical
make git-check
```

Coverage is generated with `make coverage` for integration, CLI and scripts;
per-package regression floors and a stricter notification-module gate apply.
Generated reports are temporary. `make docs-check` checks local Markdown file
links and capability catalog references; anchors and remote URLs are not checked.

## Home Assistant runtime tests

The repository includes a real Home Assistant test harness through
`pytest-homeassistant`. It creates an isolated `HomeAssistant`
instance, config-entry manager, storage directory, loader and entity/platform
lifecycle. It does not connect to Verisure: external API calls are patched with
synthetic data.

Install the development environment with:

```bash
.ha-2026.11-venv/bin/python -m pip install -r requirements-dev.txt
```

The `tzdata` dependency is required by the HA fixture for its configured IANA
zone. Run the lifecycle tests with:

```bash
.ha-2026.11-venv/bin/python -m pytest custom_components/my_verisure/tests/test_ha_lifecycle.py -q
```

These tests currently cover:

- loading the real config flow through `hass.config_entries.flow`;
- setup and unload through `hass.config_entries`;
- runtime data and composition-root isolation across two entries;
- unloading one entry while the other remains loaded;
- synthetic credentials only; no real secrets or network calls.

This harness is the first line for installation/configuration regressions. A
separate Home Assistant process or container can be added later for manual UI
and frontend validation, but Docker is not required for the deterministic
lifecycle suite.

The supported Home Assistant validation target is:

```text
Home Assistant Core 2026.11.2
Python >=3.14.2
pytest-homeassistant 2026.11.2
```

The exact target stack is declared in `requirements-ha-2026.11.txt`. Use a
separate Python 3.14 environment:

```bash
python3.14 -m venv .ha-2026.11-venv
.ha-2026.11-venv/bin/python -m pip install -r requirements-ha-2026.11.txt
PYTHONPATH="$PWD" .ha-2026.11-venv/bin/python -m pytest \
  custom_components/my_verisure/tests/test_ha_lifecycle.py -q
```

This target test has been executed successfully against Core 2026.11.2.

For a deterministic gate, use:

```bash
make test-ha-2026-11
```

The script validates the Python/Core/plugin versions and imports `PyTurboJPEG` before running the complete repository suite. Override the temporary
locations with `HA_PYTHON=/path/to/python HA_CORE=/path/to/core` when needed.

## Known gaps

- The real HA harness exercises Python lifecycle behavior, not browser/frontend interaction or physical devices.
- Provider-facing tests use synthetic HTTP responses; non-photo delivery and broader device families need separate controlled evidence.
- The 100% notification module gate is narrower than overall production coverage.

See [testing-strategy.md](../technical/testing-strategy.md) and [roadmap](../roadmap/gaps-analysis.md).
## Static typing boundary

`config_flow.py` contains one localized `type: ignore[call-arg]` on the
`ConfigFlow` subclass declaration. Home Assistant Core 2026.11.2 registers the
integration domain through `ConfigFlow.__init_subclass__(domain=...)`, while the
available typing surface exposes `object.__init_subclass__` and therefore
reports a false positive. The ignore is intentionally limited to that one
framework boundary; it is covered by the real config-flow lifecycle tests and
is not a repository-wide mypy exclusion.


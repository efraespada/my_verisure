# Testing

## Suites

| Area | Location | Notes |
|------|----------|-------|
| CLI | [`cli/tests/`](../../cli/tests/) | Commands, helpers, session |
| Embedded core | [`custom_components/my_verisure/core/tests/unit/`](../../custom_components/my_verisure/core/tests/unit/) | Repositories, use cases, DTOs, session manager |

Tests are **pytest**-based. Counts vary over time; the README historically cited ~200+ tests — run `pytest --collect-only` for current numbers.

## Useful commands

```bash
pytest custom_components/my_verisure/core/tests/unit -v
pytest cli/tests -v
```

Coverage scripts (`run_coverage.py`, `run_all_tests.py`) live at repo root.

## Home Assistant runtime tests

The repository includes a real Home Assistant test harness through
`pytest-homeassistant-custom-component`. It creates an isolated `HomeAssistant`
instance, config-entry manager, storage directory, loader and entity/platform
lifecycle. It does not connect to Verisure: external API calls are patched with
synthetic data.

Install the development environment with:

```bash
.venv/bin/python -m pip install -r requirements-dev.txt
```

The `tzdata` dependency is required by the HA fixture for its configured IANA
zone. Run the lifecycle tests with:

```bash
.venv/bin/python -m pytest custom_components/my_verisure/tests/test_ha_lifecycle.py -q
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
## Known gaps

- Limited **Home Assistant core** integration tests (no `tests/components/my_verisure` style harness in this repo).  
- End-to-end tests depend on **mocked** HTTP — see repository coverage reports for hotspots.

See [testing-strategy.md](../technical/testing-strategy.md) and [roadmap](../roadmap/gaps-analysis.md).

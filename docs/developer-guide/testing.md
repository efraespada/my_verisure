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

The supported Home Assistant validation target is:

```text
Home Assistant Core 2026.8.1
Python >=3.14.2
pytest-homeassistant-custom-component 0.13.355
```

The exact target stack is declared in `requirements-ha-2026.8.txt`. Use a
separate Python 3.14 environment:

```bash
python3.14 -m venv .ha-2026.8-venv
.ha-2026.8-venv/bin/python -m pip install -r requirements-ha-2026.8.txt
PYTHONPATH="$PWD" .ha-2026.8-venv/bin/python -m pytest \
  custom_components/my_verisure/tests/test_ha_lifecycle.py -q
```

This target test has been executed successfully against Core 2026.8.1.

For a deterministic gate, use:

```bash
make test-ha-2026-8
```

The script validates the Python, Core, pytest plugin, and `PyTurboJPEG`
versions before running the complete repository suite. Override the temporary
locations with `HA_PYTHON=/path/to/python HA_CORE=/path/to/core` when needed.

## Known gaps

- Limited **Home Assistant core** integration tests (no `tests/components/my_verisure` style harness in this repo).  
- End-to-end tests depend on **mocked** HTTP — see repository coverage reports for hotspots.

See [testing-strategy.md](../technical/testing-strategy.md) and [roadmap](../roadmap/gaps-analysis.md).

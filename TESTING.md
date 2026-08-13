# Testing and verification

This repository targets one supported runtime:

- Home Assistant Core `2026.8.1`
- Python `3.14.4` (minimum `3.14.2`)
- `pytest-homeassistant-custom-component==0.13.355`

The commands below use the interpreter selected by `HA_PYTHON` in the Makefile. The default is `/tmp/ha-2026.8.1-venv/bin/python`.

## Install the validation environment

```bash
HA_PYTHON=/tmp/ha-2026.8.1-venv/bin/python make install
```

Do not use a system Python or an unpinned Home Assistant installation for the supported gate.

## Test suites

| Area | Location | Purpose |
|---|---|---|
| CLI | `cli/tests/` | Commands, input helpers, display and CLI integration |
| Application/core | `custom_components/my_verisure/core/tests/` | Domain models, repositories, use cases, clients and lifecycle boundaries |
| Home Assistant | `custom_components/my_verisure/tests/` | Config flow, setup/unload, platforms and HA adapters |

## Canonical commands

```bash
make test                 # complete repository suite
make test-ha-2026-8       # pinned HA 2026.8.1 suite and environment checks
make test-cli             # CLI tests
make test-core            # core/application tests
make type-check           # complete mypy gate
make lint-critical        # CI syntax/import safety gate
make lint                 # complete Flake8 gate
make git-check            # compile, architecture and dependency checks
make coverage             # contextual coverage report
make ci                   # all local release gates
```

The complete suite currently includes synthetic tests only. No test calls the real Verisure API and no credential, token, OTP, auth state, log or database is stored in the repository.

## Coverage

```bash
make coverage
```

This produces a temporary `coverage.xml` and a terminal report. Remove generated reports with `make clean`. Coverage is used to identify risk hotspots; tests must validate behavior rather than inflate a percentage.

## Home Assistant lifecycle validation

`make test-ha-2026-8` validates the installed HA version, Python version, test plugin and TurboJPEG dependency before running the complete suite with the HA source checkout on `PYTHONPATH`.

The HA tests cover:

- loading the real config flow through `hass.config_entries.flow`;
- setup and unload through `hass.config_entries`;
- platform/entity lifecycle;
- synthetic API responses and failure paths;
- composition-root and entry-scoped isolation;
- unloading one entry while another remains loaded.

## Isolated manual validation

A manual UI test may be performed in a disposable Home Assistant instance using synthetic or dedicated test credentials. Do not copy real credentials, `.storage`, auth state, logs or databases into this repository. Manual validation is complementary to the deterministic test gate and must be recorded as evidence without secrets.

## Troubleshooting

- If the pinned interpreter is missing, create the environment from `requirements-ha-2026.8.txt` with Python 3.14.
- If `make test-ha-2026-8` reports a version mismatch, do not bypass the check; repair the environment or pass explicit `HA_PYTHON` and `HA_CORE` paths.
- If a test hangs, run the focused test with `-vv` and preserve the failure as a regression test rather than adding an unbounded retry.

# Testing and verification

The primary validation environment targets:

- Home Assistant Core `2026.11.2`
- Python `3.14.4` (minimum `3.14.2`)
- `pytest-homeassistant==2026.11.2`

The commands below use the interpreter selected by `HA_PYTHON` in the Makefile. The default is `<repository>/.ha-2026.11-venv/bin/python`. Activating another environment does not change it; export `HA_PYTHON` to select one.

## Install the validation environment

```bash
python3.14 -m venv .ha-2026.11-venv
make install
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
make test-ha-2026-11       # pinned HA 2026.11.2 suite and environment checks
make test-cli             # CLI tests
make test-core            # core/application tests
make type-check           # complete mypy gate
make lint-critical        # CI syntax/import safety gate
make lint                 # complete Flake8 gate
make git-check            # compile, architecture, documentation and dependency checks
make docs-check           # local Markdown file links and SDD catalog references
make coverage             # contextual coverage report
make ci                   # all local release gates
```

The complete suite currently includes synthetic tests only. No test calls the real Verisure API and no credential, token, OTP, auth state, log or database is stored in the repository.

## Coverage

```bash
make coverage
```

This measures production lines/branches across the integration, CLI and validation scripts. It enforces the notification-module gate and per-package regression floors through `scripts/check_project_coverage.py`. Successful execution removes its XML/JSON reports; `.coverage` remains an ignored local artifact. The package floors preserve the measured baseline; they are not a claim of 100% repository coverage. See [quality status](docs/quality-status.md) for the current values and denominator. Coverage is used to identify risk hotspots; tests must validate behavior rather than inflate a percentage.

## Home Assistant lifecycle validation

`make test-ha-2026-11` validates the installed HA version, Python version, test plugin and TurboJPEG dependency before running the complete suite against the installed package. Set `HA_CORE` only when deliberately validating a matching source checkout.

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

- If the pinned interpreter is missing, create the environment from `requirements-ha-2026.11.txt` with Python 3.14.
- If `make test-ha-2026-11` reports a version mismatch, do not bypass the check; repair the environment or pass explicit `HA_PYTHON` and `HA_CORE` paths.
- If a test hangs, run the focused test with `-vv` and preserve the failure as a regression test rather than adding an unbounded retry.

## Official harness bootstrap

`pytest-homeassistant==2026.11.2` registers `pytest_homeassistant.bootstrap` through
its `pytest11` entry point. It imports the fixtures before test collection; do
not register a second plugin manually or install the legacy custom-component
harness alongside it. The validation script rejects co-installation explicitly.

The `-p no:respx` setting lets HA install its HTTP aliases before the separate
respx plugin would import them; HA's own HTTP mocks remain available. The HA test
package overrides `hass_config_dir` with `hass_tmp_config_dir` to keep all writable
configuration outside the checkout. See the [official harness guide](https://pypi.org/project/pytest-homeassistant/2026.11.2/).

CI also exports the integration's installed runtime dependency closure and audits
it with pip-audit in an isolated `uv tool` environment. This does not install the
scanner into HA or override Core's exact pins. Security advisories and source
fixtures are separate checks from functional coverage.

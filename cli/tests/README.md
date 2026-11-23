# CLI tests

Use the same pinned validation environment as the integration:

```bash
python3.14 -m venv .ha-2026.11-venv
make install
make test-cli
```

Run these commands from the repository root. Export `HA_PYTHON` to select an
existing environment. `python cli/tests/run_tests.py` is a compatibility wrapper
for the same single Makefile gate and preserves its failure status.

## Current test surfaces

- `test_cli.py` and `test_integration.py`: parser, routing and process outcomes.
- `test_commands.py` and `test_command_contracts.py`: injected authentication,
  installation, alarm and camera behavior, including batch failures.
- `test_input_helpers.py` and `test_display.py`: input validation and terminal output.
- `test_repository_privacy.py`: fixture/privacy regressions.

Fixtures are synthetic and isolated. Tests do not require a user account or call
the provider. Batch paths do not prompt for missing data; ambiguous installation
selection fails without an explicit selection. Noninteractive alarm writes need
the deliberate `--no-confirm` option. Camera failures propagate a failed outcome.
Those behaviors are tested through fake ports, without physical alarm commands.

`make coverage` measures CLI production lines/branches alongside integration and
scripts and enforces package regression floors. See the current
[quality record](../../docs/quality-status.md), [testing strategy](../../docs/technical/testing-strategy.md),
and [development setup](../../docs/developer-guide/setup.md). A passing suite or
coverage percentage is not proof of every provider/device scenario.

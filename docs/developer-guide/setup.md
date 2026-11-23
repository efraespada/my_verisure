# Development setup

The integration lives in `custom_components/my_verisure/`; `cli/` is a separate
adapter using the embedded application core. There is no second root `core/`.

## Pinned validation environment

From the repository root:

```bash
python3.14 -m venv .ha-2026.11-venv
make install
make test-ha-2026-11
```

`Makefile`, `./dev` and `scripts/test-ha-2026.11.sh` select
`.ha-2026.11-venv/bin/python` by default. Activating another virtual environment
alone does not change that selection. Export `HA_PYTHON` to reuse another one:

```bash
export HA_PYTHON=/path/to/validation-env/bin/python
make install
make ci
```

Dependencies are declared in `requirements-dev.txt` and
`requirements-ha-2026.11.txt`. The pinned automated target is HA Core 2026.11.2,
Python 3.14.2 or later, and pytest-homeassistant 2026.11.2.
Household evidence on HA 2026.11.2 is separate from this target.

## Verification

```bash
make test-ha-2026-11
make test-cli
make test-core
make coverage
make type-check
make lint-critical
make git-check
make distribution-check
```

`make ci` runs all release gates. `make lint` shows the full Flake8 baseline;
see [quality status](../quality-status.md) for its remaining style debt.
Pylint, Black and Ruff are not part of the declared gate.

See [testing](testing.md), [optional local HA UI](local-development.md), and
[the root testing guide](../../TESTING.md). Never copy household `.storage`,
credentials, captures or logs into the checkout.

## CLI adapter

CLI commands share the embedded application contracts. Batch mode does not open
hidden interactive prompts: authentication must already be available, and an
ambiguous installation requires `--installation-id` (a saved selection or sole
installation can be reused). Physical alarm writes additionally require the
explicit `--no-confirm` option when `--non-interactive` is set. Camera failures
return a failed command outcome, including empty or partially failed refresh
results. Check `python -m cli.main --help` with the selected interpreter before
using the CLI. Offline command tests use synthetic ports and do not change an
alarm.

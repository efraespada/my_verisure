# Development setup

## Repository layout (high level)

```
custom_components/my_verisure/   # HA integration and embedded application core
cli/                             # Optional CLI tooling
requirements-dev.txt             # Development and test dependencies
```

The Home Assistant integration imports **`custom_components.my_verisure.core`** (see [`__init__.py`](../../custom_components/my_verisure/__init__.py)).

## Python environment

```bash
python3.14 -m venv .ha-2026.8-venv
source .ha-2026.8-venv/bin/activate
pip install -r requirements-dev.txt
```

Use the pinned `requirements-dev.txt` and the Makefile targets below; there is
no second bootstrap script or legacy test runner.

## Running tests

Use the repository Makefile so every command uses the pinned Home Assistant
validation interpreter:

```bash
make test-ha-2026-8
make test-cli
make test-core
make type-check
make lint-critical
make git-check
```

The complete test and coverage commands are documented in [the root testing
guide](../../TESTING.md).

## Lint / format

Project docs mention **flake8**, **black**, **mypy** — prefer **`pyproject.toml`** / **ruff** if the repo migrates (see `.cursor/rules/python-standards.mdc`).

## Home Assistant development

For live debugging, symlink or mount `custom_components/my_verisure` into a dev HA `config/` directory and enable debug logging.

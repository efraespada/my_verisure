# Development quick start

Use the pinned offline validation environment before running a separate HA UI.
The automated target is **Home Assistant Core 2026.11.2**, Python **3.14.2+**.
Household observations on Core **2026.11.2** are recorded separately from these
synthetic automated checks.

```bash
git clone https://github.com/efraespada/my_verisure.git
cd my_verisure
python3.14 -m venv .ha-2026.11-venv
make install
make test-ha-2026-11
```

The Makefile and `./dev` use `.ha-2026.11-venv/bin/python` by default.
To reuse an external environment, export its interpreter once:

```bash
export HA_PYTHON=/path/to/validation-env/bin/python
make install
make ci
```

Useful commands:

```bash
./dev test       # Complete HA/Core/CLI suite, synthetic data only
make coverage   # Production line/branch report and notification coverage gate
make type-check
make lint-critical
make git-check
```

`make lint` displays the complete historical Flake8 baseline. `make ci` is the
canonical release gate; full formatting debt is documented in
[quality status](docs/quality-status.md).

For an optional local HA UI, see
[local development](docs/developer-guide/local-development.md).
Docker and Dev Containers are optional and have not been exercised in the
current audit. No credentials or live alarm commands are needed for the tests.
See [testing](docs/developer-guide/testing.md),
[architecture](docs/developer-guide/architecture.md), and
[contributing](CONTRIBUTING.md).

# Local development

Run the pinned synthetic checks first using [development setup](setup.md).
The primary automated baseline is HA Core **2026.11.2** on Python **3.14.2+**,
aligned with the separately observed household runtime.
Docker is optional; no live credentials or alarm commands are needed to test.

## Canonical offline checks

From the repository root:

```bash
python3.14 -m venv .ha-2026.11-venv
make install
./dev test
make ci
```

All helper verification commands delegate to `Makefile`. Select a pre-existing
environment with `export HA_PYTHON=/path/to/env/bin/python`; activating a venv
alone does not override the default. Use `make lint-critical` for the CI lint
gate and `make lint` to see the historical full baseline. Pylint, Black and
pytest-watch are not installed by the declared development requirements.

## Optional Docker UI

Docker Desktop and OrbStack can use the same helper:

```bash
./dev docker-start
# Open http://localhost:8123 and wait for startup in the logs.
./dev docker-logs
./dev docker-stop
```

New containers use `ghcr.io/home-assistant/home-assistant:2026.11.2`, publish only
on loopback, mount integration source read-only and store HA configuration in
the **`my_verisure_dev_config` named volume**. Stop/start preserves onboarding,
`.storage` and snapshots. The helper reuses an existing container rather than
deleting it. Existing containers retain their original image/storage: inspect
and back them up before migrating them. Do not remove the named volume unless
you intend to discard its private data.

Source edits require an HA process restart to reload Python modules. Stopping
and starting the Docker container does that. Integration reload alone is not a
reliable way to load changed module code. Do not expect YAML reload to reload
Python code.

The Docker runtime has not been executed during the current audit; the helper's
command routing and persistence flags have offline regression checks.

## Optional Dev Container

Open the repository with Cursor or VS Code and the **Dev Containers** extension,
then select **Reopen in Container**. The image is pinned to the same HA baseline.
Its separate `my_verisure_devcontainer_config` named volume preserves `/config`
across rebuilds; source/configuration bind mounts are read-only.
Its post-create command installs `requirements-dev.txt` in
`/opt/my-verisure-validation`, selected through `HA_PYTHON`.

Run `make test-ha-2026-11` in the container for checks. For a UI, run `./dev start`
in its terminal or use **Run Home Assistant**; it runs in the foreground with
configuration at `/config`. Open the forwarded port **8123** (host **7123**).
Stop with Ctrl+C and start again after Python changes. `./dev config` runs the
configuration check, and `./dev logs` follows the local log.

Use the **Home Assistant (DevContainer)** debugger only after its Python
interpreter has been set to `/opt/my-verisure-validation/bin/python`.
Dev Container build/start is not part of this audit's executed evidence.

## Optional host Python UI

After installing the pinned environment:

```bash
mkdir -p config/custom_components
ln -s "$PWD/custom_components/my_verisure" config/custom_components/my_verisure
HA_CONFIG="$PWD/config" ./dev start
```

`config/` is ignored by Git. Do not copy household backups into it, and do not
share its `.storage`, credentials, logs or photos. Initial setup uses HA's UI.
Any real provider or physical alarm test needs explicit owner authorization,
permitted modes and spaced requests; this guide does not authorize one.

## Debugging and services

Use **Settings → System → Logs** for safe diagnostic messages and **Developer
Tools → States** for entity IDs. For a controlled status check, consult the
[service reference](../api-reference/services/get-status.md). Repeated status or
photo requests can trigger provider cooldown; prefer the configured polling.
The [manual validation checklist](manual-ha-verification.md) separates synthetic
lifecycle checks from household evidence.

See [architecture](../architecture/README.md), [testing](testing.md),
[contributing](../../CONTRIBUTING.md), and [API reference](../api-reference/README.md).

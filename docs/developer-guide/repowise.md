# Repowise development analysis

Repowise is integrated as an optional, development-only analysis tool. It is not a runtime dependency of the Home Assistant integration and must not be installed into the project's `.venv`, because its current dependency graph conflicts with the pinned Home Assistant test environment.

## Installation and isolation

Use the repository wrapper:

```bash
scripts/repowise.sh --version
```

The wrapper creates `.repowise-venv` on first use and installs the exact version from `requirements-repowise.txt`. The environment and Repowise's local index are ignored by Git. `REPOWISE_SKIP_EDITOR_SETUP=1` prevents machine-wide editor or MCP configuration changes.

## Baseline analysis

Run the deterministic, no-LLM baseline first:

```bash
scripts/repowise.sh init --no-prose --no-claude-md --no-codex --no-editor-setup --no-onboarding .
scripts/repowise.sh status --format json .
scripts/repowise.sh dead-code --safe-only --format json --no-workspace .
```

The output is advisory. Do not delete code solely because Repowise reports it as unused: Home Assistant registration, dynamic imports, config-entry callbacks, and CLI composition can be invisible to static analysis. Confirm every finding with repository searches, tests, and manual review.

## Deterministic analysis workflow

Refresh the local index without LLM calls:

```bash
scripts/repowise.sh update --index-only --no-workspace .
```

Then use the specialized reports according to the change under review:

```bash
scripts/repowise.sh health --format json --no-workspace .
scripts/repowise.sh health --refactoring-targets --format json --no-workspace .
scripts/repowise.sh risk --target custom_components/my_verisure/coordinator.py --format json --path .
scripts/repowise.sh context --include callers --include callees --include metrics --include health --format json --no-workspace custom_components/my_verisure/coordinator.py
scripts/repowise.sh dead-code --format md --include-internals --no-workspace .
scripts/repowise.sh security scan --history --format json --path .
scripts/repowise.sh export --format structurizr --components --no-externals /tmp/my_verisure-architecture.dsl .
```

Coverage is complementary to pytest. Generate coverage with per-test contexts when possible, then ingest it:

```bash
.venv/bin/python -m pytest --cov=custom_components/my_verisure --cov-context=test
scripts/repowise.sh coverage add --path .
scripts/repowise.sh coverage status --path . --format json
```

`impacted-tests` is most valuable for a staged or source-code change. It may return no mapping for documentation/tooling-only changes:

```bash
scripts/repowise.sh impacted-tests --staged --format json --path .
```

Do not use `ask`, `generate`, `update --docs`, or `health --generate-code` in the deterministic repository workflow: those are LLM-backed and require an explicit, separately approved provider configuration.


Repowise is currently informative and non-blocking. The existing gates remain authoritative:

- pytest;
- `compileall`;
- `scripts/architecture_guard.py`;
- critical Flake8;
- incremental mypy;
- `git diff --check`.

Promote an individual Repowise signal to a blocking gate only after a reviewed baseline demonstrates low false-positive rates for this integration.

## Privacy and safety

Do not run Repowise's LLM-backed generation commands or configure provider credentials as part of the repository setup. Do not commit `.repowise/`, generated wiki databases, editor configuration, credentials, or telemetry data. The initial integration is limited to local deterministic indexing and advisory analysis.

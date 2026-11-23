# Contributing to My Verisure

Create a `feature/` branch from **`develop`** and open a pull request targeting
`develop`. Release promotion uses a separate `develop` → `master` pull request.
Use [the issue tracker](https://github.com/efraespada/my_verisure/issues) for
reproducible bug reports and proposed changes.

## Before opening a pull request

1. Set up the [pinned validation environment](docs/developer-guide/setup.md).
2. Add behavior tests for new or changed contracts, including relevant failure,
   concurrency and cancellation paths.
3. Update user/developer documentation, README and applicable [specifications](specs/README.md).
4. Run `make ci` with the selected `HA_PYTHON` and report the results and any
   evidence limits. `make lint` also exposes historical formatting debt.
5. Describe the concrete problem, resulting behavior and validation in the PR.

Keep application policies independent of Home Assistant, HTTP, DTO and storage
implementations. Compose ports/adapters explicitly per entry; see
[architecture](docs/developer-guide/architecture.md).

Automated tests use synthetic data. Do not commit passwords, SMS codes, device
or account identifiers, tokens, household `.storage`, logs, photos or raw traffic
captures. Live alarm tests require specific owner authorization, permitted modes,
spaced calls and a dated sanitized report. A test or example is not authorization
to arm a real alarm.

Include steps to reproduce, expected/actual behavior, versions and sanitized
errors in bug reports. Contributions are licensed under the repository's
[MIT License](LICENSE).

# Quality status

Updated: 2026-08-13

## Current verified state

- Home Assistant Core: `2026.8.1`
- Python: `3.14.4`
- Home Assistant test plugin: `pytest-homeassistant-custom-component==0.13.355`
- Home Assistant suite: `505 passed` in the pinned validation environment
- Semantic/core regression slice: `375 passed`
- Mypy: no issues in `224` source files
- Critical Flake8 gate: passing
- Actionable Flake8 subset (`F401`, `F541`, `F841`): clean
- Architecture guard: passing
- Dependency check: passing
- HACS validation: passing
- GitHub Actions workflow: passing on `master`

## Full lint policy

`make lint` remains intentionally available and reports the complete Flake8
baseline. The remaining findings are primarily historical whitespace and line
length debt (`W293` and `E501`); they are not hidden by a global ignore. The CI
gate blocks syntax/import-safety findings through `make lint-critical`, while
semantic unused-code findings are kept clean.

## Evidence boundaries

The repository has not made calls to the real Verisure provider and does not
contain credentials, OTPs, tokens, sessions, logs, or databases. Docker-based
isolated Home Assistant validation remains unavailable because the current user
cannot access `/var/run/docker.sock`; host permissions were not changed.

Therefore, the following remain externally unverified: installation in a live
Home Assistant instance, real config-flow authentication, provider GraphQL
responses, refresh/rate-limit behavior, alarm commands, and real camera data.

## Source of truth

The executable gates are defined in `Makefile` and `.github/workflows/validate.yml`.
The dated execution record is `.hermes/plans/2026-08-13-completeness-execution.md`.

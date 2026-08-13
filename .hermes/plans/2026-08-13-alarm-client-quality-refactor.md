# AlarmClient quality refactor — 2026-08-13

## Goal

Reduce `AlarmClient` through real cohesive boundaries while preserving the
provider contract, Home Assistant integration behavior, entry-scoped
credentials, redacted logging, and current public client methods.

## Baseline

- `AlarmClient`: 672 lines.
- Repowise hotspot health: 4.36.
- Worst performer: `custom_components/my_verisure/core/api/alarm_client.py`.
- Full suite: 457 passed, 2 skipped.
- Mypy: 209 files without errors.
- Existing boundaries: request policy, command poller, command response
  interpreter, realtime status interpreter.

## Iterations

### 1. Status configuration boundary

Extract the alarm status configuration loading and message-to-status mapping
into an application service with explicit input/output types. It must own the
cache and fallback configuration, use injected file-loading behavior where
needed for tests, and never depend on `AlarmClient` or provider transport.

### 2. Realtime status workflow

Extract the CheckAlarm → reference ID → polling → message interpretation flow
into a coordinator/application service. The service receives credentials and a
transport port/callback, returns a typed status outcome, and owns retry policy.
`AlarmClient` remains the adapter that supplies transport and translates the
outcome to its current public dictionary contract.

### 3. Command execution workflow

Review arm/disarm orchestration after the status extraction. If a cohesive
command workflow can be extracted without merely forwarding every argument,
move response acceptance, reference validation, and poll transport ownership
behind an application boundary. Keep GraphQL request construction in the
existing request policy.

### 4. Contracts and verification

Add unit tests for each new pure/application boundary, including malformed
responses, missing references, provider errors, wait exhaustion, credentials,
and concurrent client instances. Preserve existing client contract tests and
HA service behavior.

### 5. Gates and documentation

Run the full suite, Home Assistant 2026.8.1 suite, mypy, critical Flake8,
compileall, architecture guard, pip check, diff check, and Repowise. Update
this plan with measured results and explicit limitations. Commit and push each
validated iteration.

## Non-goals

- No real Verisure calls.
- No fake provider responses presented as live validation.
- No wrapper-only extraction made solely to reduce line count.
- No broad legacy compatibility shims.

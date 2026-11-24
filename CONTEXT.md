# My Verisure project context

My Verisure is an unofficial Home Assistant integration and a CLI sharing a
provider-independent core. The official Spanish application is the protocol
reference; provider behavior and household delivery must be established with
explicit evidence rather than inferred from a successful mock.

## Domain language and invariants

- An **installation** is one alarm system. A HA **entry** owns its dependency
  graph, credentials, native device identity, storage and lifecycle tasks.
- An **alarm zone** can be interior total, interior partial day, interior partial
  night or exterior/perimeter. HA Home means exterior; Night means partial night;
  Away means total. Supplementary exterior is an independent option for interior
  commands. Never equate an unknown panel code with a known or disarmed state.
- A **reported notification** is an authenticated provider statement. A
  **confirmed result** requires an authoritative read, confirmed command result
  or verified image commit. A notification alone cannot confirm the alarm state.
- A **snapshot** is an observation with a timestamp and operation generation.
  A cached observation must not masquerade as a fresh provider confirmation.
- An **image commit** means every distinct expected photo and thumbnail was
  validated and persisted before the completion marker. A local placeholder is
  not a provider photo and must never emit `photo_ready`.
- A **cooldown** is shared by provider origin because rate blocking can affect
  the public IP. Compound commands are serialized by physical installation;
  per-entry authentication and storage remain isolated.
- Push is optional. Polling remains the fallback. No callback may cause rapid
  retry loops or repeat an alarm mutation to obtain a missing confirmation.

## Module ownership

Pure values, policies and semantic ports live in `core/application`; use cases
coordinate repository ports. Provider clients/DTOs, filesystem/Pillow code,
session persistence and dependency injection are adapters in `core`. HA entities,
config flow, coordinator and services are adapters outside `core`. The CLI is a
second adapter. See [the dependency decision](docs/adr/0001-core-and-adapter-dependencies.md).

## Evidence and maintenance

[Quality status](docs/quality-status.md) records current measured checks and
remaining limits. [SDDs](specs/README.md) describe capabilities and their
acceptance contracts. [Testing](TESTING.md) explains the pinned validation
environment. Historical live receipts are evidence for their recorded build,
not proof that every subsequent change has been installed.

The [global web/native app audit](docs/technical/2026-11-24-app-capability-audit.md)
and ten Draft SDDs describe future capability expansion. They are separate from
the five as-built baselines; source signatures and native RPC declarations are
research evidence, not implemented endpoints or permission to execute them.

Never commit account identifiers, credentials, SMS codes, native device files,
tokens, private photos or raw traffic captures. Test fixtures must be synthetic
and use temporary storage; tests must not contact the household.
